"""Constitutional status vocabularies.

WARNING ON PROVENANCE
    The live graph currently holds exactly ONE synthetic claim, so the values
    actually OBSERVED in Neo4j on 2026-08-15 were only:

        Claim.status                 {ACCEPTED}
        AdjudicationDecision.status  {RATIFIED}
        AdjudicationDecision.outcome {ACCEPT}
        CanonicalPromotion.status    {COMPLETED}
        CanonicalExecutor.status     {ACTIVE}
        AdjudicationCase.status      {DECIDED, OPEN}
        ReviewPanel.status           {ACTIVE}
        Adjudicator.status           {ACTIVE}

    Those are the happy-path values of a single smoke fixture. Treating them
    as the complete enum would be a semantic false-positive: the absence of
    REJECTED in the data is evidence about the fixture, not about the
    constitution. The sets below are therefore the INTENDED vocabulary, with
    observed members marked. Anything unmarked has never been exercised.
"""
from __future__ import annotations

# Epistemic axis — what we believe about the assertion.
CLAIM_EPISTEMIC_STATUS: frozenset[str] = frozenset({
    "SUBMITTED",
    "UNDER_REVIEW",
    "ACCEPTED",                # observed
    "ACCEPTED_WITH_DISPUTE",
    "REJECTED",
    "SUPERSEDED",
    "RETRACTED",
})

# Rights axis — whether we still hold authority over the source.
# Deliberately SEPARATE from the epistemic axis: corroboration does not create
# ownership rights, so an adjudicator cannot overturn WITHDRAWN.
CLAIM_RIGHTS_STATUS: frozenset[str] = frozenset({
    "AUTHORIZED",
    "EXPIRING",
    "EXPIRED",
    "WITHDRAWAL_PENDING",
    "WITHDRAWN",
    "RIGHTS_REVOKED",
})

# Statuses that make a claim canon-eligible; the promotion gates quantify
# over exactly this set.
CLAIM_ACCEPTED_STATUS: frozenset[str] = frozenset({
    "ACCEPTED",                # observed
    "ACCEPTED_WITH_DISPUTE",
})

DECISION_STATUS: frozenset[str] = frozenset({
    "DRAFT",
    "RATIFIED",                # observed
    "VOIDED",
})

DECISION_OUTCOME: frozenset[str] = frozenset({
    "ACCEPT",                  # observed
    "REJECT",
    "ACCEPT_WITH_DISPUTE",
})

CASE_STATUS: frozenset[str] = frozenset({
    "OPEN",                    # observed
    "DECIDED",                 # observed
    "ABANDONED",
})

PROMOTION_STATUS: frozenset[str] = frozenset({
    "PENDING",
    "COMPLETED",               # observed
    "FAILED",
    "REVERTED",
})

EXECUTOR_STATUS: frozenset[str] = frozenset({
    "ACTIVE",                  # observed
    "SUSPENDED",
    "RETIRED",
})

PANEL_STATUS: frozenset[str] = frozenset({"ACTIVE", "DISSOLVED"})       # ACTIVE observed
ADJUDICATOR_STATUS: frozenset[str] = frozenset({"ACTIVE", "SUSPENDED", "RETIRED"})

# Values proven to exist in the live graph as of 2026-08-15. Everything else
# above is specification awaiting a fixture.
OBSERVED_IN_LIVE_GRAPH: dict[str, frozenset[str]] = {
    "Claim.status": frozenset({"ACCEPTED"}),
    "AdjudicationDecision.status": frozenset({"RATIFIED"}),
    "AdjudicationDecision.outcome": frozenset({"ACCEPT"}),
    "CanonicalPromotion.status": frozenset({"COMPLETED"}),
    "CanonicalExecutor.status": frozenset({"ACTIVE"}),
    "AdjudicationCase.status": frozenset({"OPEN", "DECIDED"}),
    "ReviewPanel.status": frozenset({"ACTIVE"}),
    "Adjudicator.status": frozenset({"ACTIVE"}),
}
