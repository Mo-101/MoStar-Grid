import os
from neo4j import GraphDatabase
import json

URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
USER = os.getenv("NEO4J_USER", "neo4j")
PASSWORD = os.getenv("NEO4J_PASSWORD", "mostar123")

queries = [
    "MATCH (n:IbibioWords) RETURN keys(n) LIMIT 1",
    "MATCH (n:Neo4jAgents) RETURN keys(n) LIMIT 1",
    "MATCH (n:HealingPractices) RETURN keys(n) LIMIT 1",
    "MATCH (n:MostarMoment) RETURN keys(n) LIMIT 1"
]

def run():
    print("Connecting to Neo4j...")
    driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))
    results = {}
    with driver.session() as session:
        for q in queries:
            try:
                res = session.run(q)
                data = [dict(record) for record in res]
                results[q] = data
            except Exception as e:
                results[q] = {"error": str(e)}
                
    driver.close()
    
    with open("schema_correction_output.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print("Done")

if __name__ == "__main__":
    run()
