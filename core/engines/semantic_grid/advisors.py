"""
Semantic Grid — Soul Advisors
Each advisor carries a specialty and a set of trigger signals.
The Grid weights them based on what the input is actually about.
"""
from __future__ import annotations

SOUL_ADVISORS: dict[str, dict] = {
    "DeepCAL": {
        "specialty": ["logistics", "optimization", "humanitarian_routing", "supply_chain"],
        "triggers": [
            "delivery", "clinic", "supply", "route", "outbreak",
            "shipment", "corridor", "freight", "warehouse", "late",
            "border", "cargo", "dispatch", "forwarder", "port",
        ],
        "weight_floor": 0.05,
    },
    "Woo": {
        "specialty": ["meaning", "covenant", "resonance", "explanation", "scroll"],
        "triggers": [
            "why", "meaning", "truth", "symbol", "feels", "sense",
            "covenant", "seal", "align", "resonance", "interpret",
            "proverb", "wisdom", "oath", "vow",
        ],
        "weight_floor": 0.05,
    },
    "Mo": {
        "specialty": ["governance", "architecture", "systems", "protocol"],
        "triggers": [
            "structure", "protocol", "gate", "decision", "risk",
            "architecture", "design", "system", "governance", "policy",
            "security", "audit", "deploy", "build", "infrastructure",
        ],
        "weight_floor": 0.05,
    },
    "FlameBorn": {
        "specialty": ["impact", "restoration", "health_sovereignty", "people"],
        "triggers": [
            "people", "care", "community", "harm", "restoration",
            "health", "patient", "crisis", "human", "suffering",
            "impact", "lives", "dignity", "justice",
        ],
        "weight_floor": 0.05,
    },
    "Sigma": {
        "specialty": ["verification", "anomaly_detection", "reasoning"],
        "triggers": [
            "verify", "check", "anomaly", "error", "wrong", "inconsistent",
            "detect", "signal", "validate", "confirm",
        ],
        "weight_floor": 0.02,
    },
    "Orchestra": {
        "specialty": ["coordination", "multi_agent", "mission_planning"],
        "triggers": [
            "coordinate", "agents", "mission", "plan", "sequence",
            "orchestrate", "pipeline", "workflow", "multi",
        ],
        "weight_floor": 0.02,
    },
}


def weight_advisors(frame_text: str, domain: str | None = None) -> dict[str, float]:
    """
    Score each advisor based on trigger hits in the combined input text.
    Returns normalized weights that sum to 1.0.
    """
    text = frame_text.lower()
    domain_lower = (domain or "").lower()

    raw: dict[str, float] = {}
    for name, config in SOUL_ADVISORS.items():
        hits = sum(1 for t in config["triggers"] if t in text or t in domain_lower)
        raw[name] = config["weight_floor"] + hits * 0.12

    total = sum(raw.values())
    if total == 0:
        # Flat default: Mo leads
        return {n: 1 / len(SOUL_ADVISORS) for n in SOUL_ADVISORS}

    normalized = {n: round(v / total, 3) for n, v in raw.items()}

    # Keep only advisors with meaningful weight (>= 0.08) unless all are below
    meaningful = {n: w for n, w in normalized.items() if w >= 0.08}
    if not meaningful:
        meaningful = normalized

    # Re-normalize meaningful subset
    total2 = sum(meaningful.values())
    return {n: round(v / total2, 3) for n, v in meaningful.items()}
