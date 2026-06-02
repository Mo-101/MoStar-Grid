import os
import csv
from neo4j import GraphDatabase
import time
import sys

URI = "bolt://localhost:7687"
AUTH = ("neo4j", "Mostar123")

# Target the split nodes directory directly from the manifest export!
CSV_DIR = "/opt/mostar/mostar-grid/memory/neo4j-mindgraph/import/database_export/nodes_20260406_032038"

# The literal labels causing the runaway metric 92k bloat
FORBIDDEN = ["metric.csv", "bodylayer.csv", "mostarmoment.csv"]

def get_primary_key(headers):
    # Determine merge key:
    # Look for known APOC output markers, then UUIDs, then fallback.
    candidates = ['_id', 'id', 'uuid', 'elementId', 'node_id']
    for c in candidates:
        if c in headers:
            return c
    return headers[0] # ultimate fallback

def count_nodes(driver):
    with driver.session() as session:
        result = session.run("MATCH (n) RETURN count(n) AS c")
        return result.single()["c"]

def ingest_csv(driver, filepath, filename):
    # In APOC splits, the filename IS the exact label (e.g., MindLayer.csv)
    label = filename.replace('.csv', '')

    with open(filepath, mode='r', encoding='utf-8') as f:
        reader = csv.reader(f)
        try:
            raw_headers = next(reader)
        except StopIteration:
            return

        headers = [h.replace('\ufeff', '').strip() for h in raw_headers]
        
        # In case the file has zero actual columns or is mangled
        if not headers or len(headers) == 0:
            return

        pk = get_primary_key(headers)
        
        batch_records = []
        for row in reader:
            if not row: continue
            record = {}
            for i, val in enumerate(row):
                if i < len(headers):
                    key_clean = headers[i].strip()
                    if key_clean:
                        record[key_clean] = val
            batch_records.append(record)

        if not batch_records:
            return

        # Prepare idempotent dynamic query.
        # We wrap both the node identifier and record keys in backticks to prevent Neo4j syntax errors on hyphens or spaces!
        query = f"""
        UNWIND $batch AS record
        MERGE (n:`{label}` {{ `{pk}`: record.`{pk}` }})
        SET n += record
        """
        
        print(f"  [+] Seating {len(batch_records):>6} nodes into (:{label}) matched on `{pk}`...")
        
        start = time.time()
        with driver.session() as session:
            try:
                session.run(query, batch=batch_records)
                print(f"      -> Success ({time.time() - start:.2f}s)")
            except Exception as e:
                print(f"      -> [ERROR] Failed to merge {label}: {str(e)[:100]}")

def main():
    print(f"=== MoStar Grid Phase 2: Core Soul Extraction ===")
    print(f"Sourcing from: {CSV_DIR}")
    
    if not os.path.exists(CSV_DIR):
        print(f"\n[FATAL] Directory not found. Aborting.")
        return

    csv_files = [f for f in os.listdir(CSV_DIR) if f.endswith('.csv')]
    
    print("\n--- LABEL MATRIX (EXPORT PARSE) ---")
    valid_files = []
    total_docs = 0
    
    # Sort files for cleanliness
    csv_files.sort()
    
    for cf in csv_files:
        path = os.path.join(CSV_DIR, cf)
        sz = os.path.getsize(path) / 1024
        
        # Check against quarantine blocklist
        is_radioactive = False
        for f_banned in FORBIDDEN:
            if cf.lower() == f_banned:
                is_radioactive = True
                break
                
        if is_radioactive:
            print(f" [QUARANTINED] {cf:<22} ({sz:>6.1f} KB) -> RUNAWAY LABEL DETECTED")
        else:
            with open(path, 'r', encoding='utf-8') as f:
                row_count = sum(1 for _ in f) - 1 # exclude header
            if row_count > 0:
                print(f" [CLEAN]       {cf:<22} ({sz:>6.1f} KB) -> {row_count:>6} nodes")
                valid_files.append(cf)
                total_docs += row_count
            else:
                print(f" [EMPTY]       {cf:<22} (0 nodes)")
                
    if not valid_files:
        print("\n[!] No clean data to process. Exiting.")
        return

    print(f"\n[OK] Safe Sovereign Payload: {total_docs} nodes")
    print("\nExecuting live Neo4j injection protocol...")

    driver = GraphDatabase.driver(URI, auth=AUTH)
    try:
        driver.verify_connectivity()
    except Exception as e:
        print(f"\n[FATAL] Neo4j disconnected. {e}")
        return

    initial_count = count_nodes(driver)
    
    print(f"\n[*] Pre-Extraction Graph State: {initial_count} nodes seated.")

    for cf in valid_files:
        path = os.path.join(CSV_DIR, cf)
        ingest_csv(driver, path, cf)

    final_count = count_nodes(driver)
    print(f"\n[*] Post-Extraction Graph State: {final_count} nodes seated.")
    
    delta = final_count - initial_count
    print(f"[*] Delta Seated: + {delta} nodes.")
    
    if delta == 0 and total_docs > 0:
        print("[!] 0 delta means nodes were perfectly idempotent (they already existed!).")
    
    driver.close()
    print("\n=== Soul Layer Transferred Successfully. ===")

if __name__ == "__main__":
    main()
