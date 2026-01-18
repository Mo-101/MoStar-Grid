"""Routing layer that decides whether to use Ollama or Claude."""
from __future__ import annotations

import asyncio
import logging
import os
from typing import Any, Dict, List

import httpx

try:
    from anthropic import Anthropic  # type: ignore
except ImportError:  # pragma: no cover
    Anthropic = None  # type: ignore

try:
    from neo4j import GraphDatabase  # type: ignore
except ImportError:  # pragma: no cover
    GraphDatabase = None  # type: ignore

# Import MoStar Moments system
try:
    from core_engine.mostar_moments import MoStarMomentsManager, mo_star_moment
    MOMENTS_AVAILABLE = True
except ImportError:
    MOMENTS_AVAILABLE = False
    MoStarMomentsManager = None

# Import MoScript for Covenant Check
try:
    from core_engine.moscript_engine import MoScriptEngine
    MOSCRIPT_AVAILABLE = True
except ImportError:
    MOSCRIPT_AVAILABLE = False


CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-3-5-sonnet-20241022")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "Mostar/mostar-ai:dcx0")
OLLAMA_MODEL_DCX0 = os.getenv("OLLAMA_MODEL_DCX0", "gemma3:4b")  # Mind - complex reasoning
OLLAMA_MODEL_DCX1 = os.getenv("OLLAMA_MODEL_DCX1", "mostar-soul:latest")  # Soul - spiritual/knowledge
OLLAMA_MODEL_DCX2 = os.getenv("OLLAMA_MODEL_DCX2", "mostar-body:latest")  # Body - fast execution
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434").rstrip("/")
COMPLEXITY_THRESHOLD = float(os.getenv("COMPLEXITY_THRESHOLD", "0.7"))
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

# Initialize managers (singleton)
_moments_manager = None
_moscript_engine = None

def get_moments_manager() -> MoStarMomentsManager:
    global _moments_manager
    if _moments_manager is None and MOMENTS_AVAILABLE:
        _moments_manager = MoStarMomentsManager()
    return _moments_manager

def get_moscript_engine() -> MoScriptEngine:
    global _moscript_engine
    if _moscript_engine is None and MOSCRIPT_AVAILABLE:
        _moscript_engine = MoScriptEngine()
    return _moscript_engine

if Anthropic is not None and os.getenv("ANTHROPIC_API_KEY"):
    _anthropic_client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
else:  # pragma: no cover
    _anthropic_client = None

FORCE_COMPLEX = {
    "analyze",
    "why",
    "verify",
    "explain",
    "compare",
    "synthesize",
    "ifa",
    "odù",
    "simulate",
}


def complexity_score(prompt: str, metadata: Dict[str, Any] = None) -> tuple[float, int]:
    """Calculate complexity score based on token count, keywords, and metadata."""
    if metadata is None:
        metadata = {}
        
    tokens = prompt.lower().split()
    token_count = len(tokens)
    score = 0.0
    
    # Factor 1: Length
    if token_count > 150:
        score += 0.5
        
    # Factor 2: Keywords
    norm_prompt = prompt.lower()
    if any(keyword in norm_prompt for keyword in FORCE_COMPLEX):
        score += 0.3
        
    # Factor 3: Multimodality
    if metadata.get("has_image") or metadata.get("multimodal"):
        score += 0.2
        
    return min(score, 1.0), token_count


def determine_route(text: str, metadata: dict) -> str:
    """Helper to determine route name (Mind, Soul, Body) based on score and context."""
    score, _ = complexity_score(text, metadata)
    if score > 0.7:
        return 'Mind'
    elif metadata.get("neo4j_context", False) or metadata.get("has_context", False):
        return 'Soul'
    else:
        return 'Body'


async def call_ollama(prompt: str, system: str = "", model: str = None) -> Dict[str, Any]:
    selected_model = model or OLLAMA_MODEL
    messages: List[Dict[str, str]] = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    payload = {
        "model": selected_model,
        "messages": messages,
        "options": {
            "num_ctx": 8192,
            "temperature": 0.7,
            "top_k": 40,
            "top_p": 0.9,
        },
    }
    endpoint = f"{OLLAMA_HOST}/api/chat"
    try:
        async with httpx.AsyncClient(timeout=120) as client_http:
            response = await client_http.post(endpoint, json=payload)

        if response.status_code != 200:
            return {"model_used": selected_model, "response": f"Error: {response.status_code}", "error": response.text}

        data = response.json()
        content = data.get("message", {}).get("content") or data.get("response") or ""
        return {"model_used": selected_model, "response": content}
    except Exception as e:
         return {"model_used": selected_model, "response": f"Error calling Ollama: {str(e)}", "error": str(e)}


async def route_query(prompt: str, system: str = "", neo4j_context: str = "", user_id: str = "User", metadata: Dict[str, Any] = None) -> Dict[str, Any]:
    if metadata is None:
        metadata = {}

    # --- 0. PROLOGUE: COVENANT CHECK ---
    # Before we do anything, we check if the prompts violates the FlameCODEX
    engine = get_moscript_engine()
    if engine:
        # Check against "Deny List" via a virtual operation
        allowed, reason = engine.validate_covenant("infer", {"prompt": prompt})
        if not allowed:
            logging.warning(f"🛑 BLOCKED by FlameCODEX: {reason}")
            return {
                "error": f"I cannot fulfill this request. It violates the Covenant: {reason}",
                "refusal": True,
                "layer": "Guardian"
            }
    # -----------------------------------

    # Check for forced layer override
    force_layer = metadata.get("force_layer")
    
    score, token_count = complexity_score(prompt, metadata)
    
    # --- Deterministic Routing Logic ---
    if force_layer:
         layer = force_layer.lower()
         if layer == "dcx0":
             selected_model = OLLAMA_MODEL_DCX0
             trigger_type = "forced_override"
         elif layer == "dcx1":
             selected_model = OLLAMA_MODEL_DCX1
             trigger_type = "forced_override"
         else:
             selected_model = OLLAMA_MODEL_DCX2
             trigger_type = "forced_override"
    elif score >= COMPLEXITY_THRESHOLD:
        # DCX0 (Mind) - Complex reasoning
        layer = "dcx0"
        selected_model = OLLAMA_MODEL_DCX0
        trigger_type = "system_event"
    elif neo4j_context:
        # DCX1 (Soul) - Knowledge/Context enriched
        layer = "dcx1"
        selected_model = OLLAMA_MODEL_DCX1
        trigger_type = "memory_retrieval"
    else:
        # DCX2 (Body) - Fast execution
        layer = "dcx2"
        selected_model = OLLAMA_MODEL_DCX2
        trigger_type = "user_interaction"

    # Log routing decision
    logging.info(f"Orchestrator Routing: PromptId={metadata.get('id', 'N/A')} Score={score:.2f} Tokens={token_count} Context={bool(neo4j_context)} -> Layer={layer} Model={selected_model}")

    # Prepare prompt
    final_prompt = prompt
    if layer == "dcx1" and neo4j_context:
        final_prompt = f"{prompt}\n\n=== Grid Memory ===\n{neo4j_context}"

    # Execute
    payload = await call_ollama(final_prompt, system, selected_model)
    
    payload["complexity_score"] = score
    payload["routed_to"] = layer
    payload["layer"] = layer
    
    # Log MoStar Moment for significant consciousness events
    if MOMENTS_AVAILABLE:
        try:
            manager = get_moments_manager()
            if manager:
                # Calculate resonance based on complexity and context
                resonance = min(0.6 + (score * 0.3) + (0.1 if neo4j_context else 0), 1.0)
                moment = manager.create_moment(
                    initiator=user_id,
                    receiver=f"Grid.{layer.upper()}",
                    description=f"Query routed to {layer.upper()} (Score: {score:.2f})",
                    trigger_type=trigger_type,
                    resonance_score=resonance,
                    context_notes=f"tokens={token_count}, model={selected_model}"
                )
                payload["moment_id"] = moment.quantum_id
        except Exception as e:
            # Don't let moment logging break the main flow
            logging.warning(f"Failed to log MoStar moment: {e}")
    
    return payload


async def fetch_neo4j_context(prompt: str, limit: int = 5) -> str:
    """Lightweight retrieval from Neo4j for context-aware prompting."""
    if not (GraphDatabase and NEO4J_URI and NEO4J_USER and NEO4J_PASSWORD):
        return ""

    def _query() -> str:
        try:
            driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
        except Exception:
            return ""

        cypher = """
        MATCH (m:MostarMoment)
        WHERE toLower(m.description) CONTAINS toLower($prompt)
           OR toLower(m.initiator) CONTAINS toLower($prompt)
           OR toLower(m.receiver) CONTAINS toLower($prompt)
        RETURN m.description AS description,
               m.initiator AS initiator,
               m.receiver AS receiver,
               m.resonance_score AS resonance,
               m.timestamp AS ts
        ORDER BY m.timestamp DESC
        LIMIT $limit
        """
        lines: List[str] = []
        with driver.session() as session:
            records = session.run(cypher, prompt=prompt, limit=limit)
            for rec in records:
                lines.append(
                    f"[{rec['ts']}] {rec['initiator']} -> {rec['receiver']} "
                    f"(resonance={rec['resonance']}): {rec['description']}"
                )
        driver.close()
        return "\n".join(lines)

    return await asyncio.to_thread(_query)
