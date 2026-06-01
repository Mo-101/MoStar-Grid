from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, Optional

from .covenant import (
    GateStatus,
    TruthGate,
    EthicsGate,
    CultureGate,
    BiasGate,
    run_covenant_chain,
    CovenantLog,
    CovenantSeal
)


class Interpretation(Protocol):
    id: str  # Add ID for cryptographic sealing
    prompt: str
    resonance_score: float
    symbolic_state: str
    advisory: str
    evidence: list[str]
    requires_covenant: bool  # Concrete switch for triggering covenant


@dataclass(frozen=True)
class TruthVerdict:
    allowed: bool
    threshold: float
    score: float
    reason: str
    actions: list[str] = field(default_factory=list)
    covenant_log: Optional[CovenantLog] = None
    covenant_seal: Optional[str] = None


class TruthEngine:
    thresholds = {
        "ikang_fire": 0.75,
        "mmong_water": 0.70,
        "afim_air": 0.65,
        "isong_earth": 0.80,
    }

    blocked_states = {"discord", "fracture"}
    
    def __init__(self):
        self.covenant_gates = [
            TruthGate(),
            EthicsGate(),
            CultureGate(),
            BiasGate()
        ]

    def govern(self, interpretation: Interpretation) -> TruthVerdict:
        threshold = self.thresholds["isong_earth"]

        # 1. Base Symbolic & Resonance Checks
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
            
        # 2. Covenant Check (if triggered)
        covenant_log = None
        covenant_seal = None
        actions = ["execute"]
        reason = "TruthEngine pass: interpretation satisfies execution threshold."
        
        # We use getattr to maintain compatibility if older objects don't have the flag
        if getattr(interpretation, "requires_covenant", False):
            covenant_log = run_covenant_chain(interpretation, self.covenant_gates)
            worst_status = covenant_log.worst_status
            
            # Generate Deterministic Content-Bound Seal
            digest = covenant_log.generate_digest()
            seal = CovenantSeal(digest=digest)
            covenant_seal = seal.seal_string
            
            if worst_status == GateStatus.FAIL:
                return TruthVerdict(
                    allowed=False,
                    threshold=threshold,
                    score=interpretation.resonance_score,
                    reason=f"TruthEngine veto: Covenant Check FAILED. Seal: {covenant_seal}",
                    actions=["deny", "log_incident"],
                    covenant_log=covenant_log,
                    covenant_seal=covenant_seal
                )
            elif worst_status in (GateStatus.MONITOR, GateStatus.PASS_WITH_FLAGS):
                reason = f"TruthEngine pass (with flags): Covenant Check status {worst_status.name}. Seal: {covenant_seal}"
                actions.append("covenant_monitor")
            else:
                reason = f"TruthEngine pass: Covenant Check PASS. Seal: {covenant_seal}"

        return TruthVerdict(
            allowed=True,
            threshold=threshold,
            score=interpretation.resonance_score,
            reason=reason,
            actions=actions,
            covenant_log=covenant_log,
            covenant_seal=covenant_seal
        )
