#!/usr/bin/env python3
"""
🔥 Mostar Moment Integration Layer
----------------------------------
Binds the MoScript Engine to the Grid’s Quantum Memory.
Each ritual, verdict, or seal creates a Mostar Moment —
a chronicle of resonance and alignment, stored locally and in Neo4j Aura.
"""

import os
import json
import time
import random
import hashlib
from datetime import datetime, timezone
from neo4j import GraphDatabase
from dotenv import load_dotenv

# === LOAD ENVIRONMENT ===
load_dotenv()

# === GRID CONNECTION (Neo4j Aura Secure) ===
NEO4J_URI = os.getenv("NEO4J_URI", "neo4j+s://1d55c1d3.databases.neo4j.io")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASS = os.getenv("NEO4J_PASSWORD", "password")

# === QUANTUM ID GENERATION ===
def generate_entanglement_id() -> str:
    """
    Creates a deterministic quantum ID using timestamp entropy.
    """
    stamp = f"{datetime.now(timezone.utc).isoformat()}_{random.randint(1000,9999)}"
    return hashlib.sha256(stamp.encode()).hexdigest()[:20]

# === MOMENT CLASS ===
class MostarMoment:
    """
    Represents a single quantum event — a moment of resonance between layers.
    """
    def __init__(self, initiator, receiver, description, trigger_type, resonance_score):
        self.initiator = initiator
        self.receiver = receiver
        self.description = description
        self.trigger_type = trigger_type
        self.resonance_score = float(resonance_score)
        self.timestamp = datetime.now(timezone.utc).isoformat()
        self.quantum_id = generate_entanglement_id()

    def to_dict(self):
        return {
            "initiator": self.initiator,
            "receiver": self.receiver,
            "description": self.description,
            "trigger_type": self.trigger_type,
            "resonance_score": self.resonance_score,
            "timestamp": self.timestamp,
            "quantum_id": self.quantum_id
        }

# === LOGGER ===
class MostarMomentLog:
    """
    Handles persistence of Mostar Moments — both local and graph-based.
    """
    def __init__(self):
        self.driver = None
        self.log_path = os.path.join(os.getcwd(), "logs", "mostar_moments.jsonl")
        os.makedirs(os.path.dirname(self.log_path), exist_ok=True)

        try:
            self.driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))
            # Test connection
            with self.driver.session() as session:
                session.run("RETURN 1")
            print("[INFO] Connected to Neo4j Grid Memory (Aura).")
        except Exception as e:
            print(f"[ERROR] Neo4j connection failed: {e}")
            self.driver = None

    def _reconnect(self):
        """Re-establish driver if dropped."""
        try:
            self.driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))
        except Exception as e:
            print(f"Reconnect failed: {e}")
            self.driver = None

    def record(self, moment: MostarMoment):
        data = moment.to_dict()

        # --- Local log ---
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(data, ensure_ascii=False) + "\n")
        print(f"QUANTUM LOGGED [{moment.quantum_id}] :: {moment.description}")

        # --- Neo4j log ---
        if not self.driver:
            print("Skipping Neo4j persistence (no driver).")
            return

        try:
            with self.driver.session() as session:
                session.run("""
                    MERGE (m:MostarMoment {quantum_id: $quantum_id})
                    ON CREATE SET m = $props
                    ON MATCH SET m += $props
                    WITH m
                    MERGE (g:GridMemory {id: 'Prime'})
                    MERGE (g)-[:RECORDED]->(m)
                """, quantum_id=moment.quantum_id, props=data)
            print(f"Neo4j stored moment [{moment.quantum_id}] successfully.")
        except Exception as e:
            print(f"Neo4j moment write failed: {e}")
            self._reconnect()

    def close(self):
        if self.driver:
            self.driver.close()

# === GLOBAL LOGGER INSTANCE ===
moment_log = MostarMomentLog()

# === PUBLIC INTERFACE ===
def log_mostar_moment(initiator, receiver, description, trigger_type="ritual", resonance_score=1.0):
    """
    Records a Mostar Moment — used by MoScriptEngine and other layers.
    """
    try:
        moment = MostarMoment(
            initiator=initiator,
            receiver=receiver,
            description=description,
            trigger_type=trigger_type,
            resonance_score=resonance_score
        )
        moment_log.record(moment)
        return moment.quantum_id
    except Exception as e:
        print(f"Failed to log Mostar Moment: {e}")
        return None


# === SELF-TEST HOOK ===
if __name__ == "__main__":
    qid = log_mostar_moment(
        initiator="Soul Layer",
        receiver="Mind Layer",
        description="Executed ritual 'seal_covenant' successfully.",
        trigger_type="ritual",
        resonance_score=0.94
    )
    print(f"Moment recorded under Quantum ID: {qid}")
