import os
from neo4j import GraphDatabase
import json

URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
USER = os.getenv("NEO4J_USER", "neo4j")
PASSWORD = os.getenv("NEO4J_PASSWORD", "mostar123")

alias_queries = {
    "ibibio_word": "MATCH (n:IbibioWords) SET n:IbibioWord RETURN count(n) AS labeled",
    "healing_practice": "MATCH (n:HealingPractices) SET n:HealingPractice RETURN count(n) AS labeled",
    "agent": "MATCH (n:Neo4jAgents) SET n:Agent RETURN count(n) AS labeled",
    "moment": "MATCH (n:MostarMoment) SET n:MoStarMoment RETURN count(n) AS labeled",
    "governance": "MATCH (n:IndigenousGovernance) SET n:Governance RETURN count(n) AS labeled",
    "entity": "MATCH (n:EntityEcosystem) SET n:Entity RETURN count(n) AS labeled",
    "metric": "MATCH (n:Neo4jMetrics) SET n:Metric RETURN count(n) AS labeled",
    "task": "MATCH (n:Neo4jTasks) SET n:Task RETURN count(n) AS labeled",
    "ibibio_entry": "MATCH (n:IbibioDictionaryEntry) SET n:IbibioEntry RETURN count(n) AS labeled"
}

verify_queries = {
    "verify_ibibio": "MATCH (n:IbibioWord) RETURN count(n) AS IbibioWord",
    "verify_agent": "MATCH (n:Agent) RETURN count(n) AS Agent",
    "verify_healing": "MATCH (n:HealingPractice) RETURN count(n) AS HealingPractice",
    "verify_governance": "MATCH (n:Governance) RETURN count(n) AS Governance",
    "verify_metric": "MATCH (n:Metric) RETURN count(n) AS Metric"
}

discovery_queries = {
    "metric_keys": "MATCH (n:Neo4jMetrics) RETURN keys(n) LIMIT 1",
    "task_keys": "MATCH (n:Neo4jTasks) RETURN keys(n) LIMIT 1"
}

def run():
    print("Connecting to Neo4j...")
    driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))
    results = {"aliases": {}, "verifications": {}, "discovery": {}}
    
    with driver.session() as session:
        print("Applying aliases...")
        for name, q in alias_queries.items():
            try:
                res = session.run(q)
                results["aliases"][name] = [dict(record) for record in res]
            except Exception as e:
                results["aliases"][name] = {"error": str(e)}
                
        print("Verifying counts...")
        for name, q in verify_queries.items():
            try:
                res = session.run(q)
                results["verifications"][name] = [dict(record) for record in res]
            except Exception as e:
                results["verifications"][name] = {"error": str(e)}
                
        print("Discovering properties...")
        for name, q in discovery_queries.items():
            try:
                res = session.run(q)
                results["discovery"][name] = [dict(record) for record in res]
            except Exception as e:
                results["discovery"][name] = {"error": str(e)}

    driver.close()
    
    with open("alias_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print("Done. Saved to alias_results.json")

if __name__ == "__main__":
    run()
