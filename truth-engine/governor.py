from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol


class Interpretation(Protocol):
    prompt: str
    resonance_score: float
    symbolic_state: str
    advisory: str
    evidence: list[str]


@dataclass(frozen=True)
class TruthVerdict:
    allowed: bool
    threshold: float
    score: float
    reason: str
    actions: list[str] = field(default_factory=list)


class TruthEngine:
    thresholds = {
        "ikang_fire": 0.75,
        "mmong_water": 0.70,
        "afim_air": 0.65,
        "isong_earth": 0.80,
    }

    blocked_states = {"discord", "fracture"}

    def govern(self, interpretation: Interpretation) -> TruthVerdict:
        threshold = self.thresholds["isong_earth"]

        if interpretation.symbolic_state in self.blocked_states:
            return TruthVerdict(
                allowed=False,
                threshold=threshold,
                score=interpretation.resonance_score,
                reason=f"TruthEngine veto: symbolic state `{interpretation.symbolic_state}` requires containment review.",
                actions=["pause", "log_incident", "commander_review"],
            )

        if interpretation.resonance_score < threshold:
            return TruthVerdict(
                allowed=False,
                threshold=threshold,
                score=interpretation.resonance_score,
                reason="TruthEngine hold: resonance below Isong execution threshold.",
                actions=["hold", "request_more_context"],
            )

        return TruthVerdict(
            allowed=True,
            threshold=threshold,
            score=interpretation.resonance_score,
            reason="TruthEngine pass: interpretation satisfies execution threshold.",
            actions=["execute"],
        )
