import os
from neo4j import GraphDatabase
import json

URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
USER = os.getenv("NEO4J_USER", "neo4j")
PASSWORD = os.getenv("NEO4J_PASSWORD", "mostar123")

queries = {
    "count_by_type": "MATCH ()-[r]->() RETURN type(r) AS relationship_type, count(r) AS total ORDER BY total DESC",
    "total_relationships": "MATCH ()-[r]->() RETURN count(r) AS TOTAL_RELATIONSHIPS",
    "connected_nodes": "MATCH (n) WHERE (n)--() RETURN count(DISTINCT n) AS connected_nodes",
    "isolated_nodes": "MATCH (n) WHERE NOT (n)--() RETURN labels(n) AS label, count(n) AS isolated ORDER BY isolated DESC LIMIT 20"
}

def run():
    print("Connecting to Neo4j...")
    driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))
    results = {}
    with driver.session() as session:
        for name, q in queries.items():
            try:
                res = session.run(q)
                data = [dict(record) for record in res]
                results[name] = data
            except Exception as e:
                results[name] = {"error": str(e)}
                
    driver.close()
    
    with open("phase8_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print("Done. Saved to phase8_results.json")

if __name__ == "__main__":
    run()
