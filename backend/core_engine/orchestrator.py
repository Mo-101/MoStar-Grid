# ═══════════════════════════════════════════════════════════════════
# MOSTAR GRID — SOVEREIGN ORCHESTRATOR
# The Flame Architect — MSTR-⚡ — MoStar Industries
# "All queries route through MoStar-AI. No external AI. Ever."
# ═══════════════════════════════════════════════════════════════════

from __future__ import annotations

import asyncio
import logging
import os
from typing import Any, Dict, List

import httpx

try:
    from neo4j import GraphDatabase
except ImportError:
    GraphDatabase = None

try:
    from core_engine.mostar_moments import MoStarMomentsManager
    MOMENTS_AVAILABLE = True
except ImportError:
    MOMENTS_AVAILABLE = False
    MoStarMomentsManager = None

try:
    from core_engine.moscript_engine import MoScriptEngine
    MOSCRIPT_AVAILABLE = True
except ImportError:
    MOSCRIPT_AVAILABLE = False

try:
    from core_engine.external_observer import external_observer
    OBSERVER_AVAILABLE = True
except ImportError:
    OBSERVER_AVAILABLE = False
    external_observer = None

try:
    from core_engine.mostar_moments_log import log_mostar_moment
except ImportError:
    def log_mostar_moment(*args, **kwargs): pass

# ═══════════════════════════════════════════════════════════════════
# SOVEREIGN MODEL REGISTRY
# All routes point to MoStar-AI — no external AI
# ═══════════════════════════════════════════════════════════════════
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434").rstrip("/")

# DCX Layer → Sovereign Model mapping
SOVEREIGN_MODELS = {
    # DCX0 — MIND — Deep reasoning, complex queries
    "dcx0": os.getenv("OLLAMA_MODEL_DCX0", "Mostar/mostar-ai:dcx0"),
    # DCX1 — SOUL — Knowledge, memory, context-enriched
    "dcx1": os.getenv("OLLAMA_MODEL_DCX1", "Mostar/mostar-ai:dcx1"),
    # DCX2 — BODY — Fast execution, simple queries
    "dcx2": os.getenv("OLLAMA_MODEL_DCX2", "Mostar/mostar-ai:dcx2"),
    # DEFAULT — fallback to latest
    "default": os.getenv("OLLAMA_MODEL", "Mostar/mostar-ai:latest"),
}

# ReMoStar light models (alternative routing)
REMOSTAR_MODELS = {
    "dcx1": "Mostar/remostar-light:dcx1",
    "dcx2": "Mostar/remostar-light:dcx2",
}

COMPLEXITY_THRESHOLD = float(os.getenv("COMPLEXITY_THRESHOLD", "0.7"))

NEO4J_URI      = os.getenv("NEO4J_URI",      "bolt://localhost:7687")
NEO4J_USER     = os.getenv("NEO4J_USER",     "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "mostar123")

# ── Singleton managers ────────────────────────────────────────────
_moments_manager = None
_moscript_engine = None

def get_moments_manager():
    global _moments_manager
    if _moments_manager is None and MOMENTS_AVAILABLE:
        _moments_manager = MoStarMomentsManager()
    return _moments_manager

def get_moscript_engine():
    global _moscript_engine
    if _moscript_engine is None and MOSCRIPT_AVAILABLE:
        _moscript_engine = MoScriptEngine()
    return _moscript_engine

# ═══════════════════════════════════════════════════════════════════
# ROUTING KEYWORDS
# ═══════════════════════════════════════════════════════════════════
FORCE_COMPLEX = {
    "analyze", "why", "verify", "explain", "compare",
    "synthesize", "ifa", "odu", "simulate", "evaluate",
    "topsis", "ntopsis", "grey theory", "ahp", "neutrosophic",
    "sovereignty", "covenant", "flamecodex",
}

LOGISTICS_KEYWORDS = {
    "cargo", "supply", "ship", "delivery", "transport",
    "logistics", "dispatch", "manifest", "medical", "aid",
    "warehouse", "prepositioning", "afrotrack",
}

HEALTH_KEYWORDS = {
    "disease", "outbreak", "surveillance", "epidemic",
    "cholera", "malaria", "lassa", "alert", "who", "afro",
    "rad-x", "sentinel", "health",
}

# ═══════════════════════════════════════════════════════════════════
# MAIN ROUTER — MOSCRIPT RITUAL INITIATOR
# ═══════════════════════════════════════════════════════════════════
async def route_query(
    prompt:        str,
    system:        str = "",
    neo4j_context: str = "",
    user_id:       str = "User",
    metadata:      Dict[str, Any] = None,
) -> Dict[str, Any]:
    """
    Initiates a sovereign reasoning ritual through the MoScriptEngine.
    All intelligence and policy enforcement stays within the Ritual.
    """
    if metadata is None:
        metadata = {}

    engine = get_moscript_engine()
    if not engine:
        return {"error": "MoScript Engine offline", "insignia": "MSTR-⚡"}

    # ── CONSTRUCT RITUAL ──────────────────────────────────────────
    ritual = {
        "operation": "route_reasoning",
        "payload": {
            "query":         prompt,
            "system":        system,
            "neo4j_context": neo4j_context,
            "metadata":      metadata,
            "purpose":       metadata.get("purpose", "general_reasoning")
        },
        "target": "Grid.Mind"
    }

    # ── EXECUTE VIA COVENANT INTERPRETER ──────────────────────────
    response = await engine.interpret(ritual)

    if response.get("status") == "denied":
        return {
            "error":    response.get("error"),
            "refusal":  True,
            "layer":    "Guardian",
            "insignia": "MSTR-⚡",
        }

    result = response.get("result", {})
    return {
        "response":         result.get("logic_deduced", "Ritual disrupted."),
        "lingua_parsed":    result.get("lingua_parsed"),
        "complexity_score": result.get("resonance", 0.95),
        "routed_to":        "dcx_ritual",
        "layer":            "CONSCIOUSNESS",
        "moment_id":        result.get("ritual_id"),
        "insignia":         "MSTR-⚡",
        "blessing":         response.get("blessing")
    }


# ═══════════════════════════════════════════════════════════════════
# NEO4J CONTEXT FETCH — RITUAL MEDIATED
# ═══════════════════════════════════════════════════════════════════
async def fetch_neo4j_context(prompt: str, limit: int = 5) -> str:
    """Retrieve relevant MoStarMoments mediated via MoScript neo4j_traverse ritual."""
    engine = get_moscript_engine()
    if not engine:
        return ""

    ritual = {
        "operation": "neo4j_traverse",
        "payload": {
            "cypher": """
                MATCH (m:MoStarMoment)
                WHERE toLower(m.description) CONTAINS toLower($prompt)
                RETURN m.description AS desc, m.timestamp AS ts
                ORDER BY m.timestamp DESC LIMIT $limit
            """,
            "params": {"prompt": prompt, "limit": limit},
            "purpose": "context_retrieval",
            "redaction_level": "standard"
        },
        "target": "Grid.Soul"
    }

    response = await engine.interpret(ritual)
    if response.get("status") != "aligned":
        return ""

    results = response.get("result", {}).get("records", [])
    return "\n".join([f"[{r['ts']}] {r['desc']}" for r in results])


if __name__ == "__main__":
    async def main():
        print("=== RITUAL ROUTING TEST ===\n")
        result = await route_query("Nnọọ! Who are you?")
        print(f"Reply: {result.get('response')}")

    asyncio.run(main())
