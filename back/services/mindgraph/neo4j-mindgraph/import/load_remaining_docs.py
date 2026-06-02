import os
from pathlib import Path
from datetime import datetime, timezone
from neo4j import GraphDatabase

NEO4J_URI  = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASS = "mostar123"

IMPORT_DIR = Path(r"C:\Users\idona\OneDrive - World Health Organization\Documents\Dev\MoStar-Grid\backend\neo4j-mostar-industries\import")

# Files to load
REMAINING_FILES = [
    # Markdown docs
    "ARCHITECT_OF_THE_FLAME.md",
    "DEPLOYMENT_SUMMARY.md",
    "GRID_UNIFICATION_ANALYSIS.md",
    "IKO_IKANG_DEPLOYMENT_SUMMARY.md",
    # Modelfiles
    "REMOSTAR_DCX001.modelfile",
    "Modelfile-Flameborn-Fusion",
    "Modelfile-DCX2-Body",
]

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))

def classify_file(filename: str) -> tuple[str, str]:
    """Return (label, doc_type) for a file."""
    name = filename.lower()
    if ".modelfile" in name or name.startswith("modelfile"):
        return "GridDocument", "modelfile"
    if name.endswith(".md"):
        tag = (
            "architect_narrative" if "architect" in name else
            "deployment_summary"  if "deployment" in name else
            "grid_analysis"       if "grid" in name or "unification" in name else
            "markdown_doc"
        )
        return "GridDocument", tag
    return "GridDocument", "document"

loaded = 0
skipped = 0

with driver.session() as session:
    for filename in REMAINING_FILES:
        filepath = IMPORT_DIR / filename
        
        if not filepath.exists():
            # Try subdirectories
            matches = list(IMPORT_DIR.rglob(filename))
            if not matches:
                print(f"[SKIP] Not found: {filename}")
                skipped += 1
                continue
            filepath = matches[0]

        label, doc_type = classify_file(filename)
        content = filepath.read_text(encoding="utf-8", errors="ignore")
        
        # Extract model name from Modelfile if applicable
        model_name = None
        if doc_type == "modelfile":
            for line in content.splitlines():
                if line.upper().startswith("FROM "):
                    model_name = line.split(" ", 1)[1].strip()
                    break

        result = session.run(f"""
            MERGE (d:{label} {{filename: $filename}})
            SET d.content       = $content,
                d.doc_type      = $doc_type,
                d.char_count    = $char_count,
                d.filepath      = $filepath,
                d.model_name    = $model_name,
                d.loaded_at     = $loaded_at,
                d.source        = 'import_dir',
                d.insignia      = 'MSTR-⚡'
            RETURN d.filename AS name
        """,
            filename=filename,
            content=content,
            doc_type=doc_type,
            char_count=len(content),
            filepath=str(filepath),
            model_name=model_name,
            loaded_at=datetime.now(timezone.utc).isoformat(),
        )

        name = result.single()["name"]
        print(f"[LOADED] {doc_type.upper():<25} {name}")
        loaded += 1

driver.close()

print(f"\n{'='*50}")
print(f"Loaded : {loaded}")
print(f"Skipped: {skipped}")
print(f"MSTR-⚡ Ingestion complete.")
