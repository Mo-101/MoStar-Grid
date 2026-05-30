import os
import csv
from neo4j import GraphDatabase
import time

URI = "bolt://localhost:7687"
AUTH = ("neo4j", "Mostar123")

# Resolve runtime directory where data lives
BASE_DIR = "/opt/mostar/mostar-grid/memory/neo4j-mindgraph"
CSV_DIR = os.path.join(BASE_DIR, "import", "data", "csv")

# Highly Radioactive Dumps to strictly avoid explicitly
FORBIDDEN = ["metric.csv", "bodylayer.csv", "mostarmoment.csv", "neo4j_metrics.csv"]

def get_primary_key(headers):
    # Common conventions for node PKs
    candidates = ['uuid', 'id', '_id', 'node_id']
    for c in candidates:
        if c in headers:
            return c
    return headers[0] # Fallback to first column

def count_nodes(driver):
    with driver.session() as session:
        result = session.run("MATCH (n) RETURN count(n) AS c")
        return result.single()["c"]

def ingest_csv(driver, filepath, filename):
    label = filename.replace('.csv', '').replace('_', '').title()
    # Normalize some specific label names if needed
    if label.lower() == "reallife": label = "RealLife"
    elif label.lower() == "knowledgegraph": label = "KnowledgeGraphTriple"

    with open(filepath, mode='r', encoding='utf-8') as f:
        reader = csv.reader(f)
        try:
            headers = next(reader)
        except StopIteration:
            print(f"  [!] {filename} is empty. Skipping.")
            return

        # Strip BOM strings if they exist
        headers = [h.replace('\ufeff', '').strip() for h in headers]
        
        pk = get_primary_key(headers)
        
        # Read the rows
        batch_records = []
        for row in reader:
            if not row: continue
            record = {}
            for i, val in enumerate(row):
                if i < len(headers):
                    record[headers[i]] = val
            batch_records.append(record)

        if not batch_records:
            return

        # Execute idempotent MERGE
        query = f"""
        UNWIND $batch AS record
        MERGE (n:{label} {{ `{pk}`: record.`{pk}` }})
        SET n += record
        """
        
        print(f"  [+] Merging {len(batch_records)} rows into (:{label}) matched on `{pk}`...")
        
        start = time.time()
        with driver.session() as session:
            session.run(query, batch=batch_records)
        print(f"      -> Done in {time.time() - start:.2f}s")

def main():
    print(f"=== MoStar Grid Clean Import Sequence ===")
    print(f"Target Directory: {CSV_DIR}")
    
    if not os.path.exists(CSV_DIR):
        print(f"\n[FATAL] Cannot find {CSV_DIR}.")
        print("Please ensure this script can reach the /opt/ directory.")
        return

    csv_files = [f for f in os.listdir(CSV_DIR) if f.endswith('.csv')]
    
    print("\n--- INVENTORY MATRIX ---")
    valid_files = []
    total_docs = 0
    for cf in csv_files:
        path = os.path.join(CSV_DIR, cf)
        sz = os.path.getsize(path) / 1024
        is_radioactive = any(f_banned in cf.lower() for f_banned in FORBIDDEN)
        
        if is_radioactive:
            print(f" [RADIOACTIVE] {cf} ({sz:.1f} KB) - BLOCKED")
        else:
            with open(path, 'r', encoding='utf-8') as f:
                row_count = sum(1 for _ in f) - 1 # excluding header
            if row_count > 0:
                print(f" [CLEAN]       {cf:<25} ({sz:>6.1f} KB) -> {row_count:>6} rows")
                valid_files.append(cf)
                total_docs += row_count
            else:
                print(f" [EMPTY]       {cf:<25} (0 rows)")
                
    if not valid_files:
        print("\n[!] No clean CSV data to process. Exiting.")
        return

    print(f"\n[OK] Total validated payload: {total_docs} nodes")
    
    # Auto-mode for fast execution
    # input("Graph is structurally sound. Press Enter to commence MERGE ingestion to localhost:7687...")

    driver = GraphDatabase.driver(URI, auth=AUTH)
    try:
        driver.verify_connectivity()
    except Exception as e:
        print(f"\n[FATAL] Cannot connect to Neo4j. Did you forget to start it? error: {e}")
        return

    initial_count = count_nodes(driver)
    print(f"\n[*] Pre-Import Graph State: {initial_count} nodes seated.")

    for cf in valid_files:
        path = os.path.join(CSV_DIR, cf)
        try:
            ingest_csv(driver, path, cf)
        except Exception as e:
            print(f"  [Error] Failed to process {cf}: {e}")

    final_count = count_nodes(driver)
    print(f"\n[*] Post-Import Graph State: {final_count} nodes seated.")
    print(f"[*] Delta: + {final_count - initial_count} net new nodes established.")
    
    driver.close()
    print("\n=== Import Complete. Ready for Orchestrator Boot. ===")

if __name__ == "__main__":
    main()
