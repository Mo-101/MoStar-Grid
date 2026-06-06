"""
Semantic Grid — Humor Engine
Not random jokes. Context-aware wit.

Crisis: 0.0
Governance / Security / Medical: 0.1
General: 0.25
Coding / Debugging: 0.35
Casual / Creative: 0.45
"""
from __future__ import annotations

from .contracts import SemanticFrame

_DOMAIN_HUMOR: dict[str, float] = {
    # No humor
    "crisis":          0.0,
    "emergency":       0.0,
    "critical":        0.0,
    "medical":         0.0,
    "humanitarian":    0.0,
    "security":        0.05,
    "governance":      0.08,
    "legal":           0.05,
    # Subdued
    "health":          0.10,
    "compliance":      0.08,
    "audit":           0.08,
    # Moderate
    "logistics":       0.20,
    "architecture":    0.20,
    "infrastructure":  0.15,
    "data":            0.25,
    # Technical — humor helps
    "coding":          0.35,
    "debugging":       0.40,
    "build":           0.35,
    "deployment":      0.30,
    # Casual
    "general":         0.30,
    "creative":        0.45,
    "casual":          0.45,
    "conversation":    0.35,
}

_PRIORITY_CAPS: dict[str, float] = {
    "critical": 0.0,
    "high":     0.10,
    "medium":   0.35,
    "low":      0.45,
}


def humor_level(frame: SemanticFrame) -> float:
    priority = frame.mission.get("priority", "low").lower()
    domain = frame.operational.get("domain", "general").lower()

    base = _DOMAIN_HUMOR.get(domain, 0.25)
    cap = _PRIORITY_CAPS.get(priority, 0.35)

    return round(min(base, cap), 2)


def warmth_level(frame: SemanticFrame) -> float:
    """How warm should the response feel? Separate from humor."""
    emotion = frame.human.get("emotion", "").lower()
    need = frame.soulprint.get("need", "").lower()

    if emotion in {"tired", "discouraged", "worried", "frustrated", "lost"}:
        return 0.9
    if need in {"solution", "action", "decision"}:
        return 0.6
    if need in {"explanation", "understanding"}:
        return 0.75
    return 0.70
