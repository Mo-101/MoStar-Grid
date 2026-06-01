from neo4j import GraphDatabase
import sys

URI = "bolt://localhost:47687"

print("Testing connection with auth=None ...")
try:
    driver = GraphDatabase.driver(URI, auth=None)
    driver.verify_connectivity()
    print("--> SUCCESS! Connected without authentication.")
    driver.close()
    sys.exit(0)
except Exception as e:
    print(f"--> FAILED: {e}")

sys.exit(1)
