import os
from phantom_ingest import PhantomIngestor
from phantom_queries import PhantomQueries

def run_test():
    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    user = os.getenv("NEO4J_USER", "neo4j")
    password = os.getenv("NEO4J_PASSWORD", "Mogrid101")
    
    mock_payload = {
        "id": "epi_risk_2026_w22_maiduguri",
        "location": "Maiduguri",
        "week_id": "2026-W22",
        "fire_score": 0.78,
        "disease_floor": 0.76,
        "sealed": True,
        "covenant_seal": "mo-covenant-seal-v1-abcdef123456",
        "signal_ids": ["signal_101", "signal_102"],
        "drift_metrics": [
            {
                "id": "drift_001",
                "metric": "weight_decay_rate",
                "severity": "medium",
                "detected_at": "2026-05-30T10:00:00Z"
            }
        ],
        "dissent": [
            {
                "id": "dissent_001",
                "analyst": "Analyst_A",
                "reason": "Fire score overestimates rural risk based on field data.",
                "timestamp": "2026-05-31T09:00:00Z"
            }
        ]
    }
    
    print("Testing Ingestion...")
    ingestor = PhantomIngestor(uri, user, password)
    try:
        ingestor.ingest_phantom_payload(mock_payload)
        print("Ingestion Successful!")
    except Exception as e:
        print(f"Ingestion Failed: {e}")
    finally:
        ingestor.close()
        
    print("\nTesting Queries...")
    queries = PhantomQueries(uri, user, password)
    try:
        print("1. Risk in Maiduguri:")
        print(queries.get_risk_by_location("Maiduguri", "2026-W22"))
        
        print("\n2. Critical Corridors:")
        print(queries.get_critical_corridors_by_impact("2026-W22"))
        
        print("\n3. Recent Drift:")
        print(queries.get_recent_model_drift())
        
        print("\n4. Dissent Ledger:")
        print(queries.get_dissent_ledger())
    except Exception as e:
        print(f"Query execution failed: {e}")
    finally:
        queries.close()

if __name__ == "__main__":
    run_test()
