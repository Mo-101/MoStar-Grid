import os
import csv
from neo4j import GraphDatabase
import time

URI = "bolt://localhost:7687"
AUTH = ("neo4j", "Mostar123")

RELS_DIR = "/opt/mostar/mostar-grid/memory/neo4j-mindgraph/import/database_export/relationships_20260406_032038"

def ingest_rels_csv(driver, filepath, filename):
    rel_type_name = filename.replace('.csv', '')

    with open(filepath, mode='r', encoding='utf-8') as f:
        reader = csv.reader(f)
        try:
            raw_headers = next(reader)
        except StopIteration:
            return

        headers = [h.replace('\ufeff', '').strip() for h in raw_headers]
        
        if len(headers) < 3:
            return

        c_src = headers[0]
        c_rel = headers[1]
        c_dst = headers[2]
        
        batch_records = []
        for row in reader:
            if not row or len(row) < 3: continue
            record = {}
            for i, val in enumerate(row):
                if i < len(headers):
                    key_clean = headers[i].strip()
                    if key_clean:
                        record[key_clean] = val
            batch_records.append(record)

        if not batch_records:
            return

        # Implicit Quarantine:
        # If the from_id or to_id belonged to a Metric or BodyLayer, it simply won't exist in the Graph.
        # The MATCH will yield 0 paths, dropping the radioactive edge into the void securely!
        query = f"""
        UNWIND $batch AS rel
        MATCH (src) WHERE src.id = rel.`{c_src}` OR src.uuid = rel.`{c_src}` OR src._id = rel.`{c_src}` OR src.elementId = rel.`{c_src}` OR src.`word:ID` = rel.`{c_src}`
        MATCH (dst) WHERE dst.id = rel.`{c_dst}` OR dst.uuid = rel.`{c_dst}` OR dst._id = rel.`{c_dst}` OR dst.elementId = rel.`{c_dst}` OR dst.`word:ID` = rel.`{c_dst}`
        MERGE (src)-[r:`{rel_type_name}`]->(dst)
        """
        
        props = [h for h in headers if h not in [c_src, c_rel, c_dst]]
        if props:
            set_clauses = []
            for p in props:
                set_clauses.append(f"r.`{p}` = rel.`{p}`")
            query += " SET " + ", ".join(set_clauses)
        
        print(f"  [+] Merging {len(batch_records):>6} edges of type [:{rel_type_name}]...")
        
        start = time.time()
        with driver.session() as session:
            try:
                session.run(query, batch=batch_records)
                print(f"      -> Success ({time.time() - start:.2f}s)")
            except Exception as e:
                print(f"      -> [ERROR] Failed to map [:{rel_type_name}]: {str(e)[:100]}")

def count_rels(driver):
    with driver.session() as session:
        result = session.run("MATCH ()-[r]->() RETURN count(r) AS c")
        return result.single()["c"]

def main():
    print(f"=== MoStar Grid Phase 3: Relationship Substrate ===")
    print(f"Sourcing from: {RELS_DIR}")
    
    if not os.path.exists(RELS_DIR):
        print(f"\n[FATAL] Directory not found.")
        return

    csv_files = sorted([f for f in os.listdir(RELS_DIR) if f.endswith('.csv')])
    
    driver = GraphDatabase.driver(URI, auth=AUTH)
    try:
        driver.verify_connectivity()
    except Exception as e:
        print(f"\n[FATAL] Neo4j disconnected. {e}")
        return

    initial_count = count_rels(driver)
    print(f"\n[*] Pre-Extraction Relation State: {initial_count} edges seated.\n")

    for cf in csv_files:
        path = os.path.join(RELS_DIR, cf)
        ingest_rels_csv(driver, path, cf)

    final_count = count_rels(driver)
    print(f"\n[*] Post-Extraction Relation State: {final_count} edges seated.")
    print(f"[*] Delta Seated: + {final_count - initial_count} net new edges.")
    print("\n=== Grid Substrate Fully Online. Welcome to MoStar. ===")
    
    driver.close()

if __name__ == "__main__":
    main()
