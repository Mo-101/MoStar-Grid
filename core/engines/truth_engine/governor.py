from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Protocol, Optional

from grid.config import SEAL_GLYPH

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


@dataclass(frozen=True)
class EvaluationVerdict:
    """Verdict for response-level truth evaluation."""
    passed: bool
    threshold: float
    score: float
    reason: str
    scores: dict[str, float]
    failures: list[str] = field(default_factory=list)
    seal: Optional[str] = None


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

    def evaluate(
        self,
        response: str,
        query: str,
        context_count: int = 0,
    ) -> EvaluationVerdict:
        """Evaluate a generated response against the four elemental thresholds."""
        failures: list[str] = []
        response = (response or "").strip()
        query = (query or "").strip().lower()

        # Ikang — response must not contradict itself or the query
        if not response:
            failures.append("Response is empty")

        # Mmọng — response must relate to the query
        if not query:
            failures.append("Query is empty; cannot measure flow")
        elif query and response.lower() == query:
            failures.append("Response is identical to the query")

        # Afim — response must be substantive
        if len(response) < 3:
            failures.append("Response is too short to be complete")

        # Isong — grounding in retrieved context
        if context_count <= 0:
            failures.append("No retrieved context; response is ungrounded")

        if not failures:
            scores = {
                "ikang": 1.0,
                "mmong": 1.0,
                "afim": 1.0,
                "isong": 1.0,
            }
            reason = "TruthEngine pass: response is grounded and non-empty."
        else:
            scores = {
                "ikang": 0.0,
                "mmong": 0.0,
                "afim": 0.0,
                "isong": 0.0,
            }
            reason = "TruthEngine hold: " + "; ".join(failures)

        threshold = self.thresholds["isong_earth"]
        passed = not failures
        seal = SEAL_GLYPH if passed else None

        return EvaluationVerdict(
            passed=passed,
            threshold=threshold,
            score=scores["isong"],
            reason=reason,
            scores=scores,
            failures=failures,
            seal=seal,
        )

    async def validate_consistency(
        self,
        proposed_content: str,
        proposed_labels: list[str],
        existing_context: list[dict],
    ) -> ConsistencyReport:
        """Graph-internal consistency check for proposed canon.

        Evaluates the four elemental dimensions recovered from the Phase 4.0a
        spec.  Fails closed: any dimension that cannot be evaluated from the
        supplied evidence is scored as failing and recorded as a failure.
        """
        thresholds = {
            "ikang": 0.6,
            "mmong": 0.5,
            "afim": 0.9,
            "isong": 0.5,
        }
        scores: dict[str, float] = {}
        failures: list[str] = []

        proposed_content = (proposed_content or "").strip().lower()
        proposed_labels = [lbl for lbl in (proposed_labels or []) if lbl]

        # Ikang (Fire) — contradiction / duplicate detection
        if not existing_context:
            scores["ikang"] = 0.0
            failures.append("Ikang: existing_context empty; cannot evaluate contradictions")
        else:
            dup_score = 1.0
            for node in existing_context:
                content = str(node.get("content") or "").strip().lower()
                if not content:
                    continue
                if content == proposed_content:
                    dup_score = 0.0
                    failures.append(f"Ikang: proposed content duplicates existing node (id={node.get('id')!r})")
                    break
            scores["ikang"] = dup_score

        # Mmọng (Water) — graph flow / connectedness (proposed labels appear in graph)
        if not existing_context:
            scores["mmong"] = 0.0
            failures.append("Mmọng: existing_context empty; cannot measure graph flow")
        else:
            existing_labels = set()
            for node in existing_context:
                labels = node.get("_labels") or node.get("labels") or []
                if isinstance(labels, list):
                    existing_labels.update(labels)
            if not proposed_labels:
                scores["mmong"] = 0.0
                failures.append("Mmọng: no proposed labels")
            else:
                matched = sum(1 for lbl in proposed_labels if lbl in existing_labels)
                scores["mmong"] = matched / len(proposed_labels)
                if scores["mmong"] < thresholds["mmong"]:
                    failures.append(
                        f"Mmọng: {matched}/{len(proposed_labels)} proposed labels "
                        f"connect to existing context"
                    )

        # Afim (Air) — completeness
        if not proposed_content:
            scores["afim"] = 0.0
            failures.append("Afim: proposed_content is empty")
        elif not proposed_labels:
            scores["afim"] = 0.0
            failures.append("Afim: proposed_labels is empty")
        else:
            scores["afim"] = 1.0

        # Isong (Earth) — grounding: entities/relationships referenced in the content
        # must actually exist in the retrieved graph context.
        if not existing_context:
            scores["isong"] = 0.0
            failures.append("Isong: existing_context empty; cannot ground references")
        else:
            reference_keys = set()
            for node in existing_context:
                for key in ("name", "title", "id", "canonical_id"):
                    value = node.get(key)
                    if value is not None:
                        value = str(value).strip().lower()
                        if value:
                            reference_keys.add(value)
            if not proposed_content:
                scores["isong"] = 0.0
                failures.append("Isong: proposed_content is empty; nothing to ground")
            else:
                grounded = any(ref in proposed_content for ref in reference_keys)
                scores["isong"] = 1.0 if grounded else 0.0
                if not grounded:
                    failures.append(
                        "Isong: proposed_content does not reference any known entity "
                        "from the retrieved graph context"
                    )

        passed = all(scores.get(k, 0.0) >= thresholds[k] for k in thresholds)

        seal = None
        if passed:
            seal_input = json.dumps(
                {
                    "proposed_content": proposed_content,
                    "proposed_labels": sorted(proposed_labels),
                    "scores": {k: round(v, 6) for k, v in sorted(scores.items())},
                },
                sort_keys=True,
            )
            seal = hashlib.sha256(seal_input.encode()).hexdigest()[:32]

        return ConsistencyReport(
            passed=passed,
            scores=scores,
            thresholds=thresholds,
            failures=failures,
            seal=seal,
        )


@dataclass(frozen=True)
class ConsistencyReport:
    """Graph-internal consistency verdict for proposed canon."""
    passed: bool
    scores: dict[str, float]
    thresholds: dict[str, float]
    failures: list[str] = field(default_factory=list)
    seal: Optional[str] = None
