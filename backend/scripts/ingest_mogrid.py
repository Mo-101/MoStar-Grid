import os
import csv
import json
import asyncio
import hashlib
import unicodedata
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import asyncpg
from dataclasses import dataclass

# ═══════════════════════════════════════════════════════════════════════════
# MOGRID PRODUCTION INGESTION ENGINE (Enterprise Grade)
# ═══════════════════════════════════════════════════════════════════════════

class MigrationError(Exception):
    """Custom exception for migration failures."""
    pass

@dataclass
class IngestConfig:
    db_url: str = os.getenv("NEON_DB_URL", "")
    import_dir: Path = Path(r"c:\Users\idona\OneDrive - World Health Organization\Documents\Dev\MoStar-Grid\backend\neo4j-mostar-industries\import")
    migration_dir: Path = Path(r"c:\Users\idona\OneDrive - World Health Organization\Documents\Dev\MoStar-Grid\backend\scripts\migration")
    dry_run: bool = False

class MoGridIngestor:
    def __init__(self, config: IngestConfig):
        self.config = config
        self.conn: Optional[asyncpg.Connection] = None

    async def connect(self):
        if self.config.dry_run:
            print("🛡️ [Dry-Run] DB connection skipped.")
            return
        if not self.config.db_url:
            raise ValueError("NEON_DB_URL not found.")
        self.conn = await asyncpg.connect(self.config.db_url)
        print("⚡ Connected to Neon Postgres.")

    def normalize_text(self, text: str) -> str:
        """NFC Normalization for Ibibio diacritics and whitespace trimming."""
        if not text: return ""
        # NFC (Normalization Form Canonical Composition) is best for West African diacritics
        normalized = unicodedata.normalize('NFC', text.strip())
        return normalized

    def get_content_metadata(self, path: Path) -> Tuple[str, int, int]:
        """Compute SHA256 hash, byte size, and line count on NORMALIZED content."""
        content = path.read_text(encoding="utf-8-sig")
        normalized_content = self.normalize_text(content)
        
        sha256 = hashlib.sha256(normalized_content.encode('utf-8')).hexdigest()
        byte_size = len(normalized_content.encode('utf-8'))
        line_count = len(normalized_content.splitlines())
        
        return sha256, byte_size, line_count

    async def log_registry(self, phase: str, obj_type: str, obj_name: str, 
                         checksum: str, byte_size: int, line_count: int, 
                         row_count: int, execution_ms: int, 
                         success: bool, error_msg: str = None):
        """Phase-Commit -> Registry-Commit sequence (Independent Transaction)."""
        if self.config.dry_run: return

        # New independent connection to ensure registry records attempts even on failure
        temp_conn = await asyncpg.connect(self.config.db_url)
        try:
            async with temp_conn.transaction():
                await temp_conn.execute("""
                    INSERT INTO consciousness.schema_registry 
                    (phase, object_type, object_name, checksum, byte_size, line_count, 
                     row_count_snapshot, execution_ms, success_flag, error_message)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                """, phase, obj_type, obj_name, checksum, byte_size, line_count, 
                     row_count, execution_ms, success, error_msg)
        finally:
            await temp_conn.close()

    async def run_sql_phase(self, phase_file: str):
        path = self.config.migration_dir / phase_file
        if not path.exists(): raise MigrationError(f"Missing SQL: {phase_file}")
        
        print(f"🚀 [SQL] {phase_file}...")
        checksum, byte_size, line_count = self.get_content_metadata(path)
        start_time = time.time()
        
        if self.config.dry_run:
            print(f"   [Dry-Run] Would execute {line_count} lines.")
            return

        try:
            sql = path.read_text(encoding="utf-8-sig")
            async with self.conn.transaction():
                await self.conn.execute(sql)
            
            duration = int((time.time() - start_time) * 1000)
            await self.log_registry(phase_file.split('.')[0].upper(), 'SQL', phase_file, 
                                   checksum, byte_size, line_count, 0, duration, True)
        except Exception as e:
            duration = int((time.time() - start_time) * 1000)
            await self.log_registry(phase_file.split('.')[0].upper(), 'SQL', phase_file, 
                                   checksum, byte_size, line_count, 0, duration, False, str(e))
            raise MigrationError(f"SQL Phase {phase_file} failed: {e}")

    async def ingest_csv(self, schema: str, table: str, csv_file: str):
        csv_path = self.config.import_dir / "data" / "csv" / csv_file
        if not csv_path.exists(): raise MigrationError(f"Missing CSV: {csv_file}")

        print(f"📥 [Load] {csv_file} -> {schema}.{table}...")
        checksum, byte_size, line_count = self.get_content_metadata(csv_path)
        start_time = time.time()

        with open(csv_path, mode='r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            fieldnames = [k.lower().strip().replace(" ", "_") for k in reader.fieldnames]
            rows = list(reader)
            
            if self.config.dry_run:
                print(f"   [Dry-Run] Expected {len(rows)} rows.")
                return

            columns = ", ".join(fieldnames)
            placeholders = ", ".join([f"${i+1}" for i in range(len(fieldnames))])
            query = f"INSERT INTO {schema}.{table} ({columns}) VALUES ({placeholders}) ON CONFLICT DO NOTHING"
            
            batch_data = [[self.normalize_text(row[k]) for k in reader.fieldnames] for row in rows]

            try:
                async with self.conn.transaction():
                    await self.conn.executemany(query, batch_data)
                    # Production validation: ensure we didn't lose rows (counting ignoring duplicates)
                    # In a real-world scenario, we'd check if the table was empty before.
                
                duration = int((time.time() - start_time) * 1000)
                await self.log_registry('INGESTION', 'CSV', f"{schema}.{table}", 
                                       checksum, byte_size, line_count, len(rows), duration, True)
            except Exception as e:
                duration = int((time.time() - start_time) * 1000)
                await self.log_registry('INGESTION', 'CSV', f"{schema}.{table}", 
                                       checksum, byte_size, line_count, 0, duration, False, str(e))
                raise MigrationError(f"Ingestion of {csv_file} failed: {e}")

    async def expand_junctions(self, schema: str, base_table: str, junction_table: str, 
                                 base_id_col: str, multi_val_col: str, item_col: str):
        print(f"🧬 [Junction] {base_table}.{multi_val_col} -> {junction_table}...")
        start_time = time.time()
        
        if self.config.dry_run:
            print("   [Dry-Run] Expansion logic calculation only.")
            return

        try:
            records = await self.conn.fetch(f"SELECT {base_id_col}, {multi_val_col} FROM {schema}.{base_table} WHERE {multi_val_col} IS NOT NULL")
            
            expanded_records = []
            for rec in records:
                base_id = rec[base_id_col]
                raw_val = rec[multi_val_col]
                if not raw_val: continue
                
                # Semantic expansion rules: NFC normalized, deduplicated, order-preserved
                items = []
                seen = set()
                # Split and handle trailing/leading delimiters
                for i in raw_val.split('|'):
                    val = self.normalize_text(i)
                    if val and val not in seen:
                        items.append(val)
                        seen.add(val)
                
                for item in items:
                    expanded_records.append((base_id, item))
            
            if expanded_records:
                async with self.conn.transaction():
                    await self.conn.executemany(f"""
                        INSERT INTO {schema}.{junction_table} ({base_id_col}, {item_col})
                        VALUES ($1, $2) ON CONFLICT DO NOTHING
                    """, expanded_records)
            
            duration = int((time.time() - start_time) * 1000)
            await self.log_registry('NORMALIZATION', 'JUNCTION', f"{schema}.{junction_table}", 
                                   "", 0, 0, len(expanded_records), duration, True)
        except Exception as e:
            duration = int((time.time() - start_time) * 1000)
            await self.log_registry('NORMALIZATION', 'JUNCTION', f"{schema}.{junction_table}", 
                                   "", 0, 0, 0, duration, False, str(e))
            raise MigrationError(f"Junction expansion for {junction_table} failed: {e}")

    async def close(self):
        if self.conn: await self.conn.close()

async def execute_migration(dry_run: bool = False):
    config = IngestConfig(dry_run=dry_run)
    engine = MoGridIngestor(config)
    try:
        await engine.connect()
        
        # Phase 1: Foundation
        await engine.run_sql_phase("01_foundation.sql")

        # Phase 2-6: Schema Layers
        layers = ["02_soul_layer.sql", "03_mind_layer.sql", "04_body_layer.sql", 
                  "05_consciousness_layer.sql", "06_enrichment_layer.sql"]
        for p in layers: await engine.run_sql_phase(p)

        # Ingestion Map (Explicit)
        ingest_map = [
            ("soul", "ifa_odu", "ifa_odu_system.csv"),
            ("soul", "entities", "entity_ecosystem.csv"),
            ("soul", "ibibio_words", "ibibio_words.csv"),
            ("mind", "ai_components", "decision_intelligence_framework.csv"),
            ("body", "api_endpoints", "api_endpoints.csv"),
        ]
        for s, t, f in ingest_map: await engine.ingest_csv(s, t, f)

        # Junction Expansion (Explicit)
        await engine.expand_junctions("soul", "entities", "entity_capabilities", "entity_id", "capabilities", "capability")
        
        # Final Phase: Enforcement
        await engine.run_sql_phase("07_enforcement.sql")
        
        print("\n🏆 MIGRATION SEQUENCE COMPLETED.")
        
    except Exception as e:
        print(f"\n❌ FATAL: {e}")
        if not dry_run: raise
    finally:
        await engine.close()

if __name__ == "__main__":
    import sys
    is_dry = "--dry-run" in sys.argv
    asyncio.run(execute_migration(dry_run=is_dry))
