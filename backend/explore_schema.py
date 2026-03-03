import os
from neo4j import GraphDatabase
import json

URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
USER = os.getenv("NEO4J_USER", "neo4j")
PASSWORD = os.getenv("NEO4J_PASSWORD", "mostar123")

queries = [
    "MATCH (n:IfaMajorOdu) RETURN keys(n) LIMIT 1",
    "MATCH (n:IfaCompoundOdu) RETURN keys(n) LIMIT 1",
    "MATCH (n:IbibioWord) RETURN keys(n) LIMIT 1",
    "MATCH (n:IbibioAudio) RETURN keys(n) LIMIT 1",
    "MATCH (n:Agent) RETURN keys(n) LIMIT 1",
    "MATCH (n:AfricanPhilosophies) RETURN keys(n) LIMIT 1",
    "MATCH (n:HealingPractice) RETURN keys(n) LIMIT 1",
    "MATCH (n:MedicinalPlants) RETURN keys(n) LIMIT 1",
    "MATCH (n:Culture) RETURN keys(n) LIMIT 1",
    "MATCH (n:MoStarMoment) RETURN keys(n) LIMIT 1",
    "MATCH (n:MostarApiDoc) RETURN keys(n) LIMIT 1",
    "MATCH (n:GridDocument) RETURN keys(n) LIMIT 1",
    "MATCH (n) UNWIND labels(n) AS lbl RETURN lbl, count(*) AS cnt ORDER BY cnt DESC",
    "MATCH (w:IbibioWord) RETURN w.word, w.english, w.audio_file LIMIT 5",
    "MATCH (a:IbibioAudio) RETURN a.filename, a.word, a.audio_file LIMIT 5",
    "MATCH (n:IfaMajorOdu) RETURN n.name, n.binary, n.decimal, n.binary_code LIMIT 3",
    "MATCH (n:IfaCompoundOdu) RETURN n.name, n.combined_odu, n.binary_code, n.decimal LIMIT 3",
    "MATCH (n:Agent) RETURN n.name, n.agent_id, n.domain, n.category LIMIT 3",
    "MATCH (n:AfricanPhilosophies) RETURN n.name, n.domain, n.culture, n.category LIMIT 3",
    "MATCH (n:Culture) RETURN n.name, n.domain, n.category LIMIT 3",
    "MATCH (n:HealingPractice) RETURN n.name, n.category, n.domain, n.cultural_element LIMIT 3"
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
    
    with open("schema_output.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print("Done. Saved to schema_output.json")

if __name__ == "__main__":
    run()
