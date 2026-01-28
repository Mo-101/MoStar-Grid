import uuid
import datetime
import os
from neo4j import GraphDatabase

# Get Neo4j connection details from environment
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "neo4j")

# Initialize Neo4j driver
driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

def log_mostar_moment(initiator: str, receiver: str, description: str, trigger_type: str, resonance_score: float):
    """
    Logs a Mostar Moment, representing an interaction or event within the Grid.
    Persists the moment to Neo4j graph database.
    """
    quantum_id = str(uuid.uuid4())
    timestamp = datetime.datetime.now().isoformat()

    moment_data = {
        "quantum_id": quantum_id,
        "timestamp": timestamp,
        "initiator": initiator,
        "receiver": receiver,
        "description": description,
        "trigger_type": trigger_type,
        "resonance_score": resonance_score
    }

    try:
        with driver.session() as session:
            session.run(
                "CREATE (m:MostarMoment {quantum_id: $quantum_id, timestamp: $timestamp, "
                "initiator: $initiator, receiver: $receiver, description: $description, "
                "trigger_type: $trigger_type, resonance_score: $resonance_score})",
                moment_data
            )
            print(f"🧠 Neo4j stored moment [{quantum_id[:8]}] successfully.")
            return quantum_id
    except Exception as e:
        print(f"❌ Failed to store moment in Neo4j: {e}")
        # Fallback to local log
        print(f"🌌 QUANTUM LOGGED [Fallback] :: {moment_data}")
        return quantum_id
