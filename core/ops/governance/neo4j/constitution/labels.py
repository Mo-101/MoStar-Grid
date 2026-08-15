"""Constitutional node labels.

Verified present in the live graph on 2026-08-15 (see migrations/
000_current_governance_baseline.cypher for the reconciliation note).
"""
from __future__ import annotations

# Labels that carry constitutional force. A relationship touching any of these
# must use a type from GOVERNANCE_RELATIONSHIPS.
GOVERNANCE_LABELS: frozenset[str] = frozenset({
    "Claim",
    "ReviewPanel",
    "Adjudicator",
    "AdjudicationCase",
    "AdjudicationDecision",
    "AdjudicationVote",
    "CanonicalPromotion",
    "CanonicalExecutor",
    "AuthorizationDecision",
    "Testimony",
    "Attestor",
    "Institution",
    "KnowledgeBoundary",
})

# Separation of duties. An executor must not also be an adjudicator: the
# promotion gates assert `NOT 'Adjudicator' IN labels(executor)`.
MUTUALLY_EXCLUSIVE_LABELS: tuple[tuple[str, str], ...] = (
    ("CanonicalExecutor", "Adjudicator"),
)

# Every constitutional node is identified by `canonical_id`, backed by a
# uniqueness constraint (13 such constraints exist live).
IDENTITY_PROPERTY = "canonical_id"
