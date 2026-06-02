"""Ontology placement ranking for Phase 4.0a canon proposals."""
from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass
from typing import Any


@dataclass
class PlacementOption:
    labels: list[str]
    properties: dict[str, Any]
    relationships: list[dict]
    confidence: float
    reasoning: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class PlacementRanking:
    options: list[PlacementOption]
    selected: int
    canon_input_hash: str

    def to_dict(self) -> dict:
        return {
            "options": [option.to_dict() for option in self.options],
            "selected": self.selected,
            "canon_input_hash": self.canon_input_hash,
        }


class DecisionEngine:
    async def rank_placement(
        self,
        interpretation,
        existing_context: list[dict],
        consistency_report,
    ) -> PlacementRanking:
        content = getattr(interpretation, "canon_input", "") or getattr(interpretation, "reasoning", "")
        labels = self._labels_for(interpretation)
        ontology_score = self._ontology_score(labels, existing_context)
        relationship_score = min(1.0, len(getattr(interpretation, "relationships", [])) * 0.2)
        truth_score = sum(consistency_report.scores.values()) / max(1, len(consistency_report.scores))
        semantic_score = min(1.0, len(existing_context) / 10)
        confidence = (
            ontology_score * 0.3
            + relationship_score * 0.25
            + truth_score * 0.25
            + semantic_score * 0.2
        )

        option = PlacementOption(
            labels=labels,
            properties={
                "content": content,
                "category": getattr(interpretation, "category", "canon"),
                "entities": getattr(interpretation, "entities", []),
            },
            relationships=getattr(interpretation, "relationships", []),
            confidence=round(confidence, 3),
            reasoning=(
                "Ranked from ontology label fit, relationship density, "
                "TruthEngine consistency, and nearby graph context."
            ),
        )
        return PlacementRanking(
            options=[option],
            selected=0,
            canon_input_hash=hashlib.sha256(content.encode("utf-8")).hexdigest(),
        )

    @staticmethod
    def _labels_for(interpretation) -> list[str]:
        category = getattr(interpretation, "category", "canon") or "canon"
        if category.lower() in {"agent", "person"}:
            return ["Agent", "GridKnowledge"]
        if category.lower() in {"rollback", "reversal"}:
            return ["Rollback", "GridKnowledge"]
        return ["Memory", "GridKnowledge"]

    @staticmethod
    def _ontology_score(labels: list[str], existing_context: list[dict]) -> float:
        existing_labels = {
            label
            for node in existing_context
            for label in node.get("_labels", [])
            if isinstance(node.get("_labels", []), list)
        }
        if not existing_labels:
            return 0.65
        return len(set(labels) & existing_labels) / max(1, len(labels))
