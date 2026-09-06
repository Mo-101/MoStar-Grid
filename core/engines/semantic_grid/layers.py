"""
Semantic Grid — Layer Extraction
Parses raw human input into five semantic layers using DCX0-Mind (phi4).

Falls back to keyword heuristics if the LLM is unavailable.
The five layers:
  1. Literal     — what was literally said
  2. Operational — what problem domain this belongs to
  3. Human       — emotion, fear, stakeholders
  4. Mission     — what must be preserved or accomplished
  5. Soulprint   — user type, need, response style
"""
from __future__ import annotations

import json
import logging
import re

import httpx
from grid.mind_conduit_runtime import OLLAMA_GENERATE_PATH, governed_http_post, invoke_model

logger = logging.getLogger("semantic_grid.layers")

_LAYER_PROMPT = """\
You are the MoStar Semantic Grid. Your job is to extract meaning from human input.

Analyze the following input and return ONLY valid JSON with exactly this structure:

{{
  "literal": {{
    "entity": "<the main thing being talked about>",
    "condition": "<what is happening to it>",
    "action": "<what action is implied, if any>"
  }},
  "operational": {{
    "problem": "<the functional problem>",
    "domain": "<one of: logistics|health|governance|architecture|security|coding|medical|humanitarian|general|creative|conversation>",
    "urgency": "<low|medium|high|critical>"
  }},
  "human": {{
    "fear": "<what the person is afraid of or worried about>",
    "emotion": "<one of: neutral|focused|worried|tired|frustrated|urgent|curious|discouraged|confident>",
    "stakeholders": ["<who is affected>"]
  }},
  "mission": {{
    "mission": "<what must be preserved or accomplished>",
    "priority": "<low|medium|high|critical>"
  }},
  "soulprint": {{
    "user_type": "<one of: operator|builder|leader|thinker|caregiver>",
    "need": "<one of: solution|explanation|decision|action|validation|conversation>",
    "response_style": "<one of: direct|detailed|gentle|concise>"
  }}
}}

Input: "{input}"

Return ONLY the JSON object. No markdown. No explanation. No commentary."""


_FALLBACK_DOMAINS = {
    "clinic": "health", "hospital": "health", "patient": "health", "medical": "medical",
    "delivery": "logistics", "shipment": "logistics", "freight": "logistics",
    "route": "logistics", "border": "logistics", "supply": "logistics",
    "deploy": "coding", "build": "coding", "debug": "coding", "code": "coding",
    "risk": "governance", "policy": "governance", "protocol": "governance",
    "crisis": "humanitarian", "outbreak": "humanitarian", "emergency": "humanitarian",
    "why": "conversation", "feel": "conversation", "meaning": "conversation",
}

_FALLBACK_URGENCY = {
    "late": "high", "urgent": "critical", "critical": "critical",
    "emergency": "critical", "immediately": "high", "asap": "high",
    "slow": "medium", "delayed": "medium",
}

_FALLBACK_EMOTION = {
    "late": "worried", "broken": "frustrated", "wrong": "frustrated",
    "help": "worried", "stuck": "tired", "lost": "discouraged",
    "great": "confident", "excited": "focused",
}


def _fallback_extract(raw_input: str) -> dict:
    """Keyword heuristic extraction when LLM is unreachable."""
    text = raw_input.lower()
    words = re.findall(r"\b\w+\b", text)

    domain = "general"
    for word in words:
        if word in _FALLBACK_DOMAINS:
            domain = _FALLBACK_DOMAINS[word]
            break

    urgency = "medium"
    for word in words:
        if word in _FALLBACK_URGENCY:
            urgency = _FALLBACK_URGENCY[word]
            break

    emotion = "neutral"
    for word in words:
        if word in _FALLBACK_EMOTION:
            emotion = _FALLBACK_EMOTION[word]
            break

    priority = urgency if urgency in {"high", "critical"} else "medium"

    return {
        "literal": {
            "entity": words[0] if words else "unknown",
            "condition": " ".join(words[1:3]) if len(words) > 1 else "",
            "action": "",
        },
        "operational": {
            "problem": raw_input[:80],
            "domain": domain,
            "urgency": urgency,
        },
        "human": {
            "fear": "",
            "emotion": emotion,
            "stakeholders": [],
        },
        "mission": {
            "mission": raw_input[:80],
            "priority": priority,
        },
        "soulprint": {
            "user_type": "operator",
            "need": "solution",
            "response_style": "direct",
        },
    }


async def extract_layers(
    raw_input: str,
    ollama_url: str = "http://localhost:11434",
    model: str = "phi4:latest",
) -> tuple[dict, str]:
    """
    Extract all five semantic layers from raw_input.

    Returns (layers_dict, extraction_source) where source is "llm" or "fallback".
    layers_dict has keys: literal, operational, human, mission, soulprint.
    """
    prompt = _LAYER_PROMPT.format(input=raw_input.replace('"', "'"))

    try:
        async with httpx.AsyncClient(base_url=ollama_url, timeout=20.0) as client:
            payload = {
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.1, "num_predict": 512},
                }
            resp = await invoke_model(
                caller="semantic_grid.extract_layers",
                model_id=model,
                snapshot_identity="semantic-input:no-memory",
                adapter=lambda context: governed_http_post(
                    context, client, OLLAMA_GENERATE_PATH, payload
                ),
            )
            resp.raise_for_status()
            raw_text = resp.json().get("response", "").strip()

        # Strip markdown fences if model wrapped the JSON
        raw_text = re.sub(r"^```(?:json)?\s*", "", raw_text)
        raw_text = re.sub(r"\s*```$", "", raw_text)

        layers = json.loads(raw_text)

        # Validate structure — all five keys must be present
        required = {"literal", "operational", "human", "mission", "soulprint"}
        if not required.issubset(layers.keys()):
            raise ValueError(f"Missing keys: {required - layers.keys()}")

        return layers, "llm"

    except Exception as exc:
        logger.warning("Layer extraction LLM failed (%s) — using fallback", exc)
        return _fallback_extract(raw_input), "fallback"
