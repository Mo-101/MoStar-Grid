#!/usr/bin/env python3
"""
📡 MOSTAR GRID — CANONICAL TELEMETRY v3
Provides unified, MoScript-governed telemetry for the Hyper-Spine Dashboard.
Transforms backend data into the canonical API schema, utilizing purely sealed traversals.
"""

import os
import asyncio
from datetime import datetime, timezone
import logging
from .moscript_engine import MoScriptEngine

log = logging.getLogger("MoStarTelemetry")

class CanonicalTelemetryEngine:
    def __init__(self, engine: MoScriptEngine = None):
        self.mo = engine or MoScriptEngine()

    async def _safe_traverse(self, cypher: str, purpose: str, target: str = "Grid.Mind"):
        ritual = {
            "operation": "neo4j_traverse",
            "payload": {
                "cypher": cypher,
                "purpose": purpose,
                "redaction_level": "standard"
            },
            "target": target
        }
        res = await self.mo.interpret(ritual)
        if res.get("status") == "aligned":
            return res.get("result", {}).get("records", [])
        return []

    async def get_grid_telemetry(self) -> dict:
        """
        Gathers Grid telemetry using MoScript-governed Neo4j traversals
        and formats it into Canonical Telemetry v3.
        """
        # --- 1. Grid State ---
        grid_state_cypher = """
            MATCH (m:MoStarMoment)
            RETURN avg(coalesce(m.resonance_score, 0.85)) as avg_resonance,
                   max(m.timestamp) as last_cycle
        """
        grid_state_records = await self._safe_traverse(grid_state_cypher, "telemetry_grid_state")
        
        avg_resonance = 0.85
        last_cycle = datetime.now(timezone.utc).isoformat()
        if grid_state_records:
            avg_resonance = float(grid_state_records[0].get("avg_resonance") or 0.85)
            last_cycle = grid_state_records[0].get("last_cycle") or last_cycle

        # Calculate a pseudo confidence based on resonance threshold
        confidence = min(100.0, max(0.0, avg_resonance * 100 + 5.0))

        # --- 2. Agents ---
        agents_cypher = """
            MATCH (a:Agent)
            RETURN coalesce(a.agent_id, a.id, elementId(a)) AS id,
                   a.name AS name,
                   coalesce(a.manifestationStrength, 50.0) AS manifestationStrength,
                   coalesce(a.status, 'online') AS status,
                   a.task_count AS task_count
            ORDER BY a.name ASC
            LIMIT 500
        """
        agents_records = await self._safe_traverse(agents_cypher, "telemetry_agents", "Grid.Body")
        
        agents = []
        for a in agents_records:
            agents.append({
                "id": a.get("id"),
                "name": a.get("name"),
                "manifestationStrength": float(a.get("manifestationStrength", 50.0)),
                "status": str(a.get("status", "online")),
                "provenance": {"task_count": a.get("task_count", 0)}
            })

        # --- 3. Moments ---
        # Fetch generic recent
        recent_cypher = """
            MATCH (m:MoStarMoment)
            RETURN m.quantum_id AS id, m.description AS desc, m.layer AS layer, m.resonance_score AS res, m.timestamp as ts
            ORDER BY m.timestamp DESC LIMIT 15
        """
        recent_moments_raw = await self._safe_traverse(recent_cypher, "telemetry_recent_moments")
        
        # Categorized moments
        soul_cypher = """MATCH (m:MoStarMoment {layer: 'SOUL'}) RETURN m.quantum_id AS id, m.description AS desc ORDER BY m.timestamp DESC LIMIT 5"""
        soul_raw = await self._safe_traverse(soul_cypher, "telemetry_soul_moments", "Grid.Soul")

        mind_cypher = """MATCH (m:MoStarMoment {layer: 'MIND'}) RETURN m.quantum_id AS id, m.description AS desc ORDER BY m.timestamp DESC LIMIT 5"""
        mind_raw = await self._safe_traverse(mind_cypher, "telemetry_mind_moments", "Grid.Mind")
        
        body_cypher = """MATCH (m:MoStarMoment {layer: 'BODY'}) RETURN m.quantum_id AS id, m.description AS desc ORDER BY m.timestamp DESC LIMIT 5"""
        body_raw = await self._safe_traverse(body_cypher, "telemetry_body_moments", "Grid.Body")

        canonical_payload = {
            "gridState": {
                "resonance": float(f"{avg_resonance:.4f}"),
                "confidence": float(f"{confidence:.2f}"),
                "lastCycle": last_cycle
            },
            "agents": agents,
            "moments": {
                "recent": [dict(m) for m in recent_moments_raw],
                "soulMoments": [dict(m) for m in soul_raw],
                "mindMoments": [dict(m) for m in mind_raw],
                "bodyMoments": [dict(m) for m in body_raw]
            }
        }
        
        # Seal the payload
        canonical_payload["seal"] = self.mo.bless("canonical_telemetry")

        return canonical_payload

async def get_grid_telemetry():
    """Async wrapper for the external world to call."""
    engine = CanonicalTelemetryEngine()
    return await engine.get_grid_telemetry()

def get_grid_telemetry_sync():
    """Sync wrapper if needed."""
    return asyncio.run(get_grid_telemetry())
