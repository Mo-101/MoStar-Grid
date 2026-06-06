"""
Semantic Grid — Contracts
Core data structures. These are the shapes meaning takes inside MoStar.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

Persona = Literal[
    "COMMANDER",
    "ARCHITECT",
    "TEACHER",
    "GUARDIAN",
    "COMPANION",
    "ORACLE",
]


@dataclass
class SemanticState:
    """Living per-user state that persists across turns."""
    user_id: str
    current_mission: str | None = None
    current_emotion: str | None = None
    urgency_level: int = 0          # 0–10
    trust_level: float = 0.5        # 0.0–1.0
    decision_mode: str = "observer"
    focus_area: str | None = None
    updated_at: str | None = None

    def to_dict(self) -> dict:
        return {
            "user_id": self.user_id,
            "current_mission": self.current_mission,
            "current_emotion": self.current_emotion,
            "urgency_level": self.urgency_level,
            "trust_level": self.trust_level,
            "decision_mode": self.decision_mode,
            "focus_area": self.focus_area,
            "updated_at": self.updated_at,
        }


@dataclass
class SemanticFrame:
    """
    The full meaning envelope for one input.

    Five layers of interpretation + advisor weights + persona + policy.
    This is what the Grid knows before it opens its mouth.
    """
    raw_input: str
    user_id: str = ""
    source: str = "text"

    # ── Five semantic layers ──────────────────────────────────────────
    literal: dict[str, Any] = field(default_factory=dict)
    operational: dict[str, Any] = field(default_factory=dict)
    human: dict[str, Any] = field(default_factory=dict)
    mission: dict[str, Any] = field(default_factory=dict)
    soulprint: dict[str, Any] = field(default_factory=dict)

    # ── Synthesis ─────────────────────────────────────────────────────
    advisor_weights: dict[str, float] = field(default_factory=dict)
    persona: Persona = "ARCHITECT"
    humor_level: float = 0.25

    # ── Response shape ────────────────────────────────────────────────
    response_policy: dict[str, Any] = field(default_factory=lambda: {
        "warmth": 0.7,
        "clarity": 1.0,
        "humor": 0.25,
        "risk_mode": "normal",
    })

    # ── Meta ──────────────────────────────────────────────────────────
    frame_id: str = ""
    created_at: str = ""
    extraction_source: str = "llm"   # "llm" | "fallback"
    truth_passed: bool | None = None
    woo_state: str | None = None

    def to_dict(self) -> dict:
        return {
            "frame_id": self.frame_id,
            "user_id": self.user_id,
            "source": self.source,
            "raw_input": self.raw_input,
            "literal": self.literal,
            "operational": self.operational,
            "human": self.human,
            "mission": self.mission,
            "soulprint": self.soulprint,
            "advisor_weights": self.advisor_weights,
            "persona": self.persona,
            "humor_level": self.humor_level,
            "response_policy": self.response_policy,
            "extraction_source": self.extraction_source,
            "truth_passed": self.truth_passed,
            "woo_state": self.woo_state,
            "created_at": self.created_at,
        }
