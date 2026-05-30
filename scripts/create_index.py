from neo4j import GraphDatabase
import os

try:
    driver = GraphDatabase.driver('bolt://localhost:47687', auth=('neo4j', '<REDACTED>'))
    with driver.session(database='neo4j') as session:
        session.run("CREATE FULLTEXT INDEX gridSearch IF NOT EXISTS FOR (n:GridKnowledge) ON EACH [n.content, n.name, n.action, n.intent, n.reasoning]")
        print("Index created")
except Exception as e:
    print("Error:", e)
