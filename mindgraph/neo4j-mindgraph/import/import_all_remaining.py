import os
import csv
import json
from neo4j import GraphDatabase

# === CONFIG ===
IMPORT_DIR = r"C:\Users\AI\Documents\MoStar\Mo Docs\neo4j-community-2025.10.1\import"
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASS = "mostar123"

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))

# === CSV LOADER ===
def load_csv(filename, label):
    full_path = os.path.join(IMPORT_DIR, filename)
    with open(full_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            props = {k: v for k, v in row.items() if v}
            name = props.get('name') or props.get('id') or os.path.splitext(filename)[0]
            with driver.session() as session:
                session.run(
                    f"MERGE (n:{label} {{name: $name}}) SET n += $props",
                    name=name,
                    props=props
                )

# === JSON LOADER ===
def load_json(filename, label):
    full_path = os.path.join(IMPORT_DIR, filename)

    with open(full_path, encoding="utf-8") as f:
        try:
            data = json.load(f)
            if isinstance(data, dict) and "rows" in data:
                data = data["rows"]
            elif isinstance(data, list) and all(isinstance(item, str) for item in data):
                # Handle edge case: JSON array of strings
                data = [json.loads(line) for line in data]
        except json.JSONDecodeError:
            f.seek(0)
            data = [json.loads(line.strip()) for line in f if line.strip()]

    with driver.session() as session:
        for item in data:
            if isinstance(item, str):
                item = json.loads(item)  # ensure it's a dict

            word = item.get('word:ID') or item.get('word') or item.get('id')
            if word:
                session.run(
                    f"MERGE (n:{label} {{word: $word}}) SET n += $props",
                    word=word,
                    props=item
                )

# === RUN IMPORTS ===
csv_files = [
    ("african_philosophies.csv", "Philosophy"),
    ("medicinal_plants.csv", "Plant"),
    ("healing_practices.csv", "Healing"),
    ("knowledge_graph.csv", "Knowledge"),
    ("science.csv", "Science"),
    ("ethics.csv", "Ethics"),
    ("childhood.csv", "Childhood"),
    ("adulthood.csv", "Adulthood"),
    ("ibibio_words.csv", "IbibioWord")
]

for fname, label in csv_files:
    print(f"Loading {fname}...")
    load_csv(fname, label)

print("Loading ibibio_dictionary.json...")
load_json("ibibio_dictionary.json", "IbibioWord")

print("✅ ALL DONE.")
