"""
Woo Judgment System — Sovereign Decision Gate
Validates at 0.97 threshold before critical decisions pass.
Integrates with Truth Engine for compound verification.

Woo × DeepCAL Fusion: DeepCAL computes neutrosophic rankings,
Woo validates at threshold before decisions proceed.
"""
import logging
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone

from grid.config import WOO_THRESHOLD, SEAL_GLYPH
from truth_engine import TruthVerdict

logger = logging.getLogger("woo")


@dataclass
class WooJudgment:
    approved: bool
    confidence: float
    threshold: float
    truth_verdict: TruthVerdict
    reasoning: str
    judged_at: str
    seal: str = ""

    def to_dict(self) -> dict:
        return {
            "approved": self.approved,
            "confidence": self.confidence,
            "threshold": self.threshold,
            "truth_passed": self.truth_verdict.passed,
            "truth_scores": self.truth_verdict.scores,
            "reasoning": self.reasoning,
            "judged_at": self.judged_at,
            "seal": self.seal,
        }


@dataclass
class WooInterpretation:
    category: str
    entities: list[str]
    relationships: list[dict]
    confidence: float
    reasoning: str
    canon_input: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


class WooInterpreter:
    """Structural interpreter for canon ingestion proposals."""

    async def interpret(
        self,
        canon_input: str,
        graph_context: list[dict],
    ) -> WooInterpretation:
        text = canon_input.strip()
        category = self._category(text)
        entities = self._entities(text)
        relationships = self._relationships(entities, graph_context)
        confidence = min(0.95, 0.55 + len(entities) * 0.08 + len(relationships) * 0.05)
        return WooInterpretation(
            category=category,
            entities=entities,
            relationships=relationships,
            confidence=round(confidence, 3),
            reasoning="Rule-based ingestion interpretation; DCX Soul can replace this when available.",
            canon_input=text,
        )

    @staticmethod
    def _category(text: str) -> str:
        lowered = text.lower()
        if "rollback" in lowered or "reversal" in lowered:
            return "rollback"
        if "agent" in lowered:
            return "agent"
        if "canon" in lowered or "doctrine" in lowered:
            return "canon"
        return "knowledge"

    @staticmethod
    def _entities(text: str) -> list[str]:
        entities = re.findall(r"\b[A-Z][A-Za-z0-9_-]*(?:\s+[A-Z][A-Za-z0-9_-]*)*\b", text)
        seen = []
        for entity in entities:
            if entity not in seen:
                seen.append(entity)
        return seen[:10]

    @staticmethod
    def _relationships(entities: list[str], graph_context: list[dict]) -> list[dict]:
        relationships = []
        for entity in entities[:5]:
            for node in graph_context[:3]:
                target = node.get("id") or node.get("name")
                labels = node.get("_labels") if isinstance(node.get("_labels"), list) else ["GridKnowledge"]
                if target:
                    relationships.append({
                        "type": "RELATES_TO",
                        "target_label": labels[0] if labels else "GridKnowledge",
                        "target_match": {"id": target},
                        "direction": "out",
                        "entity": entity,
                    })
                    break
        return relationships


# Explicit aliases — use when you need the canon/ingestion interpreter specifically
WooCanonInterpreter = WooInterpreter
WooCanonInterpretation = WooInterpretation


class WooGate:
    """
    High-confidence judgment gate.
    Used for critical decisions — not every response.
    """

    def __init__(self, threshold: float = None):
        self.threshold = threshold or WOO_THRESHOLD

    def judge(
        self,
        truth_verdict: TruthVerdict,
        action_type: str = "response",
        override_threshold: float = None,
    ) -> WooJudgment:
        """
        Pass judgment on a truth-verified response.
        
        action_type controls when Woo fires:
        - "response": standard response, Woo auto-approves if truth passes
        - "decision": critical decision, requires full Woo threshold
        - "execution": code/deploy execution, highest bar
        """
        threshold = override_threshold or self.threshold

        # Calculate compound confidence from truth scores
        if not truth_verdict.passed:
            confidence = 0.0
            reasoning = f"Truth Gate failed: {', '.join(truth_verdict.failures)}"
        else:
            scores = truth_verdict.scores
            # Weighted compound: Earth heaviest (grounding matters most for decisions)
            confidence = (
                scores.get("ikang", 0) * 0.2 +
                scores.get("mmong", 0) * 0.2 +
                scores.get("afim", 0) * 0.25 +
                scores.get("isong", 0) * 0.35
            )
            reasoning = f"Compound confidence {confidence:.3f} from elemental scores"

        # Auto-approve standard responses if truth passed
        if action_type == "response" and truth_verdict.passed:
            approved = True
            reasoning += " — auto-approved (standard response)"
        else:
            approved = confidence >= threshold
            if not approved:
                reasoning += f" — below Woo threshold ({threshold})"

        judgment = WooJudgment(
            approved=approved,
            confidence=confidence,
            threshold=threshold,
            truth_verdict=truth_verdict,
            reasoning=reasoning,
            judged_at=datetime.now(timezone.utc).isoformat(),
            seal=SEAL_GLYPH if approved else "",
        )

        level = logging.INFO if approved else logging.WARNING
        logger.log(level, "Woo judgment: %s (%.3f) — %s",
                   "APPROVED" if approved else "REJECTED",
                   confidence, action_type)
        return judgment
