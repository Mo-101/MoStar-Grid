"""Closed constitutional relationship vocabulary.

AUTHORITATIVE. This set is the constitution's relationship grammar. Adding a
member is a constitutional amendment, not a spelling change, and requires:

    1. source change
    2. vocabulary change (this file)
    3. tests
    4. migration
    5. review

Enforcement is two-sided:

    untyped relationship pattern        -> reject   (-[]->, -[r]->, -[_TO]->)
    typed but not in this vocabulary    -> reject   (-[:PROMOTES]-> )
    typed and in this vocabulary        -> accept   (-[:PROMOTED]-> )

The second rule exists because Cypher will happily accept `PROMOTES` for
`PROMOTED`. Valid syntax is not the same as constitutional validity: a gate
written against the wrong type name executes successfully and proves nothing.
Source lint cannot see relationships created out-of-band, so it is paired with
a live-graph drift audit in core/ops/audit/neo4j/.
"""
from __future__ import annotations

# ── Promotion into canon ────────────────────────────────────────────────
PROMOTION = frozenset({
    "PROMOTED",        # CanonicalPromotion -> Claim
    "AUTHORIZED_BY",   # CanonicalPromotion -> AdjudicationDecision
    "EXECUTED_BY",     # CanonicalPromotion -> CanonicalExecutor
})

# ── Adjudication ────────────────────────────────────────────────────────
ADJUDICATION = frozenset({
    "DECIDES",         # AdjudicationDecision -> AdjudicationCase
    "REVIEWS",         # AdjudicationCase     -> Claim
    "RESOLVES",        # AdjudicationDecision -> Claim
    "ISSUED_BY",       # AdjudicationDecision -> ReviewPanel
})

# ── Panel composition and voting ────────────────────────────────────────
PANEL = frozenset({
    "ASSIGNED_TO",     # ReviewPanel -> AdjudicationCase
    "HAS_MEMBER",      # ReviewPanel -> Adjudicator
    "CAST_BY",         # AdjudicationVote -> Adjudicator
    "FOR_CASE",        # AdjudicationVote -> AdjudicationCase
    "FOR_CLAIM",       # AdjudicationVote -> Claim
    "RECUSED_FROM",    # Adjudicator -> AdjudicationCase
})

# ── Policy / governance binding ─────────────────────────────────────────
POLICY = frozenset({
    "GOVERNED_BY",
    "REQUIRES",
    "ADDRESSES",
    "APPLIES_TO",
})

# ── Provenance and attestation ──────────────────────────────────────────
PROVENANCE = frozenset({
    "ORIGINATES_FROM",
    "ATTESTED_BY",
})

# ── Epistemic relations between claims ──────────────────────────────────
EPISTEMIC = frozenset({
    "SUPERSEDES",
    "DISPUTES",
    "CORROBORATES",
    "RETRACTS",
})

# ── Derivation lineage ──────────────────────────────────────────────────
LINEAGE = frozenset({
    "DEPENDS_ON",
})

# ── Rights / obligation ─────────────────────────────────────────────────
RIGHTS = frozenset({
    "HELD_BY",
    "OWED_TO",
    "SATISFIES",
})

GOVERNANCE_RELATIONSHIPS: frozenset[str] = frozenset().union(
    PROMOTION, ADJUDICATION, PANEL, POLICY, PROVENANCE, EPISTEMIC, LINEAGE, RIGHTS,
)

assert len(GOVERNANCE_RELATIONSHIPS) == 27, (
    f"vocabulary size changed to {len(GOVERNANCE_RELATIONSHIPS)}; "
    "a constitutional amendment must update this assertion deliberately"
)
