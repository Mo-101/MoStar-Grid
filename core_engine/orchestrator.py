"""Routing layer that decides whether to use Ollama or Claude."""
from __future__ import annotations

import asyncio
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


CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-3-5-sonnet-20241022")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "akiniobong10/Mostar-REMOSTAR_DCX001")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434").rstrip("/")
COMPLEXITY_THRESHOLD = float(os.getenv("COMPLEXITY_THRESHOLD", "0.75"))
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

if Anthropic is not None and os.getenv("ANTHROPIC_API_KEY"):
    _anthropic_client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
else:  # pragma: no cover
    _anthropic_client = None

FORCE_COMPLEX = {
    "ifa",
    "odù",
    "n-ahp",
    "n-topsis",
    "grey theory",
    "neutrosophic",
    "matrix weighting",
}


def complexity_score(prompt: str) -> float:
    """Very basic heuristic — replace with your existing scorer."""
    tokens = prompt.lower()
    score = 0.3
    if any(keyword in tokens for keyword in FORCE_COMPLEX):
        return 1.0
    if len(tokens.split()) > 250:
        score += 0.2
    if "analyze" in tokens or "evaluate" in tokens:
        score += 0.2
    return min(score, 1.0)


async def call_ollama(prompt: str, system: str = "") -> Dict[str, Any]:
    messages: List[Dict[str, str]] = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    payload = {
        "model": OLLAMA_MODEL,
        "messages": messages,
        "options": {
            "num_ctx": 131_072,
            "num_predict": 8_192,
            "temperature": 0.7,
            "top_k": 40,
            "top_p": 0.9,
        },
    }
    endpoint = f"{OLLAMA_HOST}/api/chat"
    async with httpx.AsyncClient(timeout=120) as client_http:
        response = await client_http.post(endpoint, json=payload)

    if response.status_code != 200:
        raise RuntimeError(f"Ollama chat failed: {response.status_code} {response.text}")

    data = response.json()
    content = data.get("message", {}).get("content") or data.get("response") or ""
    return {"model_used": "ollama", "response": content}


async def call_claude(prompt: str, system: str = "", neo4j_context: str = "") -> Dict[str, Any]:
    if _anthropic_client is None:
        return await call_ollama(prompt, system)

    enriched = f"""{system}

=== GRID MEMORY ===
{neo4j_context}

=== USER QUERY ===
{prompt}
"""

    def _invoke():
        return _anthropic_client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=4_096,
            messages=[{"role": "user", "content": enriched}],
        )

    msg = await asyncio.to_thread(_invoke)
    return {"model_used": "claude", "response": msg.content[0].text}


async def route_query(prompt: str, system: str = "", neo4j_context: str = "") -> Dict[str, Any]:
    score = complexity_score(prompt)
    if score >= COMPLEXITY_THRESHOLD:
        payload = await call_claude(prompt, system, neo4j_context)
    else:
        payload = await call_ollama(prompt, system)
    payload["complexity_score"] = score
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
