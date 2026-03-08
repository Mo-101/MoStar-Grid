#!/usr/bin/env python3
"""
Sacred Handshake – Covenant Kernel stabilizer.
Ensures agents and executors are properly registered and trusted.
"""

import hashlib
import os
import uuid
from datetime import datetime, timezone
from core_engine.moscript_engine import MoScriptEngine
from core_engine.mostar_moments_log import log_mostar_moment

COVENANT_SECRET = os.getenv("COVENANT_SECRET", "default-change-me")  # should be a strong secret

class SacredHandshake:
    def __init__(self, engine: MoScriptEngine = None):
        self.mo = engine or MoScriptEngine()
        self.covenant_node_id = "covenant-kernel-001"

    async def register_agent(self, agent_id: str, agent_name: str, public_key: str = None) -> bool:
        """
        Register a new agent with a handshake seal.
        Returns True if registration succeeded.
        """
        # Generate a handshake signature
        timestamp = datetime.now(timezone.utc).isoformat()
        nonce = str(uuid.uuid4())
        signature = self._generate_signature(f"{agent_id}:{timestamp}:{nonce}")

        ritual = {
            "operation": "neo4j_traverse",
            "payload": {
                "cypher": """
                    MERGE (a:Agent {id: $agent_id})
                    SET a.name = $agent_name,
                        a.public_key = $public_key,
                        a.registered_at = datetime($timestamp),
                        a.handshake_nonce = $nonce,
                        a.handshake_signature = $signature,
                        a.trusted = true
                    RETURN a
                """,
                "params": {
                    "agent_id": agent_id,
                    "agent_name": agent_name,
                    "public_key": public_key,
                    "timestamp": timestamp,
                    "nonce": nonce,
                    "signature": signature
                },
                "purpose": "agent_registration",
                "redaction_level": "full"
            },
            "target": "Grid.Soul"
        }
        response = await self.mo.interpret(ritual)
        if response.get("status") == "aligned":
            log_mostar_moment(
                "SacredHandshake", "Grid.Soul",
                f"Agent registered: {agent_name} ({agent_id})",
                "agent_registration", 1.0, layer="SOUL"
            )
            return True
        else:
            log_mostar_moment(
                "SacredHandshake", "Grid.Soul",
                f"Agent registration failed: {agent_id}",
                "registration_failure", 0.2, layer="SOUL"
            )
            return False

    async def verify_executor(self, executor_id: str, challenge: str) -> bool:
        """
        Verify that an executor is trusted.
        The executor must present a challenge signed with the covenant secret.
        """
        expected = self._generate_signature(executor_id)
        if challenge == expected:
            log_mostar_moment(
                "SacredHandshake", "Grid.Soul",
                f"Executor verified: {executor_id}",
                "executor_verification", 1.0, layer="SOUL"
            )
            return True
        else:
            log_mostar_moment(
                "SacredHandshake", "Grid.Soul",
                f"Executor verification failed: {executor_id}",
                "verification_failure", 0.1, layer="SOUL"
            )
            return False

    async def check_covenant_node(self) -> bool:
        """Check that the covenant kernel node exists and is trusted."""
        ritual = {
            "operation": "neo4j_traverse",
            "payload": {
                "cypher": """
                    MATCH (c:CovenantKernel {id: $id})
                    RETURN c.trusted AS trusted
                """,
                "params": {"id": self.covenant_node_id},
                "purpose": "covenant_check",
                "redaction_level": "full"
            },
            "target": "Grid.Soul"
        }
        response = await self.mo.interpret(ritual)
        if response.get("status") != "aligned":
            return False
        records = response.get("result", {}).get("records", [])
        if not records:
            return False
        return records[0].get("trusted") == True

    def _generate_signature(self, data: str) -> str:
        """Generate a simple HMAC-like signature."""
        return hashlib.sha256(f"{data}:{COVENANT_SECRET}".encode()).hexdigest()[:16]
