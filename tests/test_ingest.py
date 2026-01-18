import pytest
import os
import json
import shutil
from pathlib import Path
from backend.memory_layer.ingest import ingest_memory, STORE_PATH

def test_ingest_lifecycle(tmp_path):
    # Setup dummy data
    source_file = tmp_path / "test_moments.json"
    data = {
        "nodes": [
            {
                "type": "MoStarMoment",
                "id": "m1",
                "data": {
                    "description": "Test Moment",
                    "era": "Experimental",
                    "resonance": 0.8,
                    "initiator": "Tester",
                    "receiver": "Grid",
                    "timestamp": "2026-01-18T00:00:00Z"
                }
            }
        ]
    }
    with open(source_file, "w") as f:
        json.dump(data, f)
        
    # Test ingestion
    # We might need to mock embeddings if they take too long or require internet
    # But for a basic logic test, we see if it processes the file
    
    # Note: ingest_memory uses global STORE_PATH. In a real test we'd patch it.
    # For now, this is a scaffold.
    pass
