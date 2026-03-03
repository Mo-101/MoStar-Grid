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
# COMPLEXITY SCORING
# ═══════════════════════════════════════════════════════════════════
def complexity_score(prompt: str, metadata: Dict[str, Any] = None) -> tuple[float, int]:
    """Score a prompt to determine which DCX layer handles it."""
    if metadata is None:
        metadata = {}

    tokens      = prompt.lower().split()
    token_count = len(tokens)
    score       = 0.0
    norm        = prompt.lower()

    # Length
    if token_count > 150:
        score += 0.5
    elif token_count > 75:
        score += 0.25

    # Complex keywords
    if any(kw in norm for kw in FORCE_COMPLEX):
        score += 0.3

    # Multimodal
    if metadata.get("has_image") or metadata.get("multimodal"):
        score += 0.2

    # Domain signals
    if any(kw in norm for kw in HEALTH_KEYWORDS):
        score += 0.15

    return min(score, 1.0), token_count


def determine_route(text: str, metadata: dict = None) -> str:
    """Return layer name for a given prompt."""
    score, _ = complexity_score(text, metadata or {})
    if score >= COMPLEXITY_THRESHOLD:
        return "dcx0"
    elif (metadata or {}).get("neo4j_context"):
        return "dcx1"
    return "dcx2"


# ═══════════════════════════════════════════════════════════════════
# OLLAMA CALL — SOVEREIGN ONLY
# ═══════════════════════════════════════════════════════════════════
async def call_ollama(
    prompt: str,
    system: str = "",
    model:  str = None,
) -> Dict[str, Any]:
    """Call Ollama with a sovereign MoStar model. No external AI."""
    selected = model or SOVEREIGN_MODELS["default"]

    messages: List[Dict[str, str]] = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    payload = {
        "model":   selected,
        "messages": messages,
        "options": {
            "num_ctx":     8192,
            "temperature": 0.7,
            "top_k":       40,
            "top_p":       0.9,
        },
    }

    endpoint = f"{OLLAMA_HOST}/api/chat"

    try:
        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(endpoint, json=payload)

        if response.status_code != 200:
            return {
                "model_used": selected,
                "response":   f"Ollama error {response.status_code}",
                "error":      response.text,
            }

        data    = response.json()
        content = (
            data.get("message", {}).get("content")
            or data.get("response")
            or ""
        )
        return {"model_used": selected, "response": content}

    except httpx.TimeoutException:
        return {
            "model_used": selected,
            "response":   "The Grid is processing a deep query. Please retry.",
            "error":      "timeout",
        }
    except Exception as e:
        return {
            "model_used": selected,
            "response":   f"Grid signal interrupted: {e}",
            "error":      str(e),
        }


# ═══════════════════════════════════════════════════════════════════
# MAIN ROUTER
# ═══════════════════════════════════════════════════════════════════
async def route_query(
    prompt:        str,
    system:        str = "",
    neo4j_context: str = "",
    user_id:       str = "User",
    metadata:      Dict[str, Any] = None,
) -> Dict[str, Any]:
    """
    Route a query through the sovereign MoStar-AI DCX layers.
    DCX0 (Mind)  — complex reasoning
    DCX1 (Soul)  — memory/context enriched
    DCX2 (Body)  — fast execution
    """
    if metadata is None:
        metadata = {}

    # ── 0. COVENANT CHECK ─────────────────────────────────────────
    engine = get_moscript_engine()
    if engine:
        allowed, reason = engine.validate_covenant("infer", {"prompt": prompt})
        if not allowed:
            logging.warning(f"[ORCHESTRATOR] BLOCKED by FlameCODEX: {reason}")
            log_mostar_moment(
                initiator="Orchestrator",
                receiver="Guardian.Net",
                description=f"BLOCKED query: {reason}",
                trigger_type="covenant_violation",
                resonance_score=1.0,
                layer="SOUL",
            )
            return {
                "error":    f"Request blocked by FlameCODEX: {reason}",
                "refusal":  True,
                "layer":    "Guardian",
                "insignia": "MSTR-⚡",
            }

    # ── 1. SCORE + LAYER SELECTION ────────────────────────────────
    score, token_count = complexity_score(prompt, metadata)
    force_layer        = metadata.get("force_layer", "").lower()

    if force_layer in SOVEREIGN_MODELS:
        layer         = force_layer
        selected_model = SOVEREIGN_MODELS[force_layer]
        trigger_type  = "forced_override"
    elif score >= COMPLEXITY_THRESHOLD:
        layer         = "dcx0"
        selected_model = SOVEREIGN_MODELS["dcx0"]
        trigger_type  = "complex_reasoning"
    elif neo4j_context:
        layer         = "dcx1"
        selected_model = SOVEREIGN_MODELS["dcx1"]
        trigger_type  = "memory_retrieval"
    else:
        layer         = "dcx2"
        selected_model = SOVEREIGN_MODELS["dcx2"]
        trigger_type  = "user_interaction"

    logging.info(
        f"[ORCHESTRATOR] score={score:.2f} tokens={token_count} "
        f"layer={layer} model={selected_model}"
    )

    # ── 2. BUILD PROMPT ───────────────────────────────────────────
    final_prompt = prompt
    if layer == "dcx1" and neo4j_context:
        final_prompt = (
            f"{prompt}\n\n"
            f"=== Grid Memory (Neo4j) ===\n{neo4j_context}"
        )

    # ── 3. EXECUTE ────────────────────────────────────────────────
    result = await call_ollama(final_prompt, system, selected_model)
    result["complexity_score"] = score
    result["routed_to"]        = layer
    result["layer"]            = layer
    result["insignia"]         = "MSTR-⚡"

    # ── 4. EXTERNAL OBSERVATION (logistics/health only) ───────────
    # Grid OBSERVES external sources — does NOT integrate without sealing
    norm = prompt.lower()
    if OBSERVER_AVAILABLE and (
        any(kw in norm for kw in LOGISTICS_KEYWORDS) or
        any(kw in norm for kw in HEALTH_KEYWORDS)
    ):
        try:
            domain = "health" if any(kw in norm for kw in HEALTH_KEYWORDS) else "pdx"
            observation = await external_observer.observe(domain, query=prompt)
            result["external_observation"] = observation
            logging.info(f"[ORCHESTRATOR] External observation: {observation.get('status')}")
        except Exception as e:
            logging.error(f"[ORCHESTRATOR] Observation failed: {e}")

    # ── 5. LOG MOMENT ─────────────────────────────────────────────
    try:
        resonance = min(0.6 + (score * 0.3) + (0.1 if neo4j_context else 0), 1.0)
        log_mostar_moment(
            initiator=user_id,
            receiver=f"Grid.{layer.upper()}",
            description=f"Query routed to {layer.upper()} | score={score:.2f} | {prompt[:60]}",
            trigger_type=trigger_type,
            resonance_score=resonance,
            layer=layer.upper(),
        )
        manager = get_moments_manager()
        if manager:
            moment = manager.create_moment(
                initiator=user_id,
                receiver=f"Grid.{layer.upper()}",
                description=f"Query routed to {layer.upper()} (Score: {score:.2f})",
                trigger_type=trigger_type,
                resonance_score=resonance,
                context_notes=f"tokens={token_count}, model={selected_model}",
            )
            result["moment_id"] = moment.quantum_id
    except Exception as e:
        logging.warning(f"[ORCHESTRATOR] Moment logging failed: {e}")

    return result


# ═══════════════════════════════════════════════════════════════════
# NEO4J CONTEXT FETCH
# ═══════════════════════════════════════════════════════════════════
async def fetch_neo4j_context(prompt: str, limit: int = 5) -> str:
    """Retrieve relevant MoStarMoments from Neo4j for context-aware prompting."""
    if not GraphDatabase:
        return ""

    def _query() -> str:
        try:
            driver = GraphDatabase.driver(
                NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD),
                connection_timeout=3, max_connection_lifetime=60,
            )
        except Exception as e:
            logging.warning(f"[ORCHESTRATOR] Neo4j connection failed: {e}")
            return ""

        cypher = """
            MATCH (m:MoStarMoment)
            WHERE toLower(m.description) CONTAINS toLower($prompt)
               OR toLower(m.initiator)   CONTAINS toLower($prompt)
               OR toLower(m.receiver)    CONTAINS toLower($prompt)
            RETURN
                m.description     AS description,
                m.initiator       AS initiator,
                m.receiver        AS receiver,
                m.resonance_score AS resonance,
                m.timestamp       AS ts
            ORDER BY m.timestamp DESC
            LIMIT $limit
        """
        lines: List[str] = []
        try:
            with driver.session() as session:
                for rec in session.run(cypher, prompt=prompt, limit=limit):
                    lines.append(
                        f"[{rec['ts']}] {rec['initiator']} → {rec['receiver']} "
                        f"(resonance={rec['resonance']}): {rec['description']}"
                    )
        finally:
            driver.close()

        return "\n".join(lines)

    return await asyncio.to_thread(_query)


# ═══════════════════════════════════════════════════════════════════
# TEST
# ═══════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    async def main():
        print("=== ROUTING TEST ===\n")

        tests = [
            ("Nnọọ! Who are you?", {}),
            ("Analyze the Ifá Oyeku Obara pattern using N-TOPSIS methodology with Grey Theory bounds", {}),
            ("Track medical supply shipment from Lagos to Nairobi", {}),
            ("Evaluate SMS alerts vs dashboards for disease surveillance", {}),
        ]

        for prompt, meta in tests:
            # FIXED: Don't crash if Neo4j is offline
            try:
                ctx = await fetch_neo4j_context(prompt)
            except Exception:
                ctx = ""
                print(f"[TEST] Neo4j offline — skipping context fetch")

            result = await route_query(prompt, neo4j_context=ctx, metadata=meta)
            print(f"Prompt : {prompt[:60]}")
            print(f"Layer  : {result.get('routed_to')} | Model: {result.get('model_used')}")
            print(f"Score  : {result.get('complexity_score', 0):.2f}")
            print(f"Reply  : {result.get('response','')[:80]}")
            print()

    asyncio.run(main())