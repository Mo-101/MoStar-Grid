// GATE A — PRESENCE-OF-GOOD (positive witness)
//
//   "Every accepted claim has at least one VALID promotion path."
//
// Verified 2026-08-15: (no records) — but over an evaluated population of
// exactly ONE synthetic accepted claim (non-test accepted claims = 0).
// Passing here is currently evidence the gate RUNS, not that the
// constitution holds at scale. See gates/README expectations.
//
// This gate alone is insufficient: it cannot detect an ADDITIONAL forged
// promotion alongside a valid one. Pair it with promotion_absence_of_bad.cypher.
//
// EXPECTED: (no records)

MATCH (cl:Claim)
WHERE cl.status IN ['ACCEPTED', 'ACCEPTED_WITH_DISPUTE']
AND NOT EXISTS {
  MATCH (promotion:CanonicalPromotion)-[:PROMOTED]->(cl)
  MATCH (promotion)-[:AUTHORIZED_BY]->(d:AdjudicationDecision)
  MATCH (promotion)-[:EXECUTED_BY]->(executor:CanonicalExecutor)

  MATCH (d)-[:DECIDES]->(c:AdjudicationCase)
  MATCH (c)-[:REVIEWS]->(cl)
  MATCH (d)-[:RESOLVES]->(cl)

  MATCH (d)-[:ISSUED_BY]->(panel:ReviewPanel)
  MATCH (panel)-[:ASSIGNED_TO]->(c)

  WHERE promotion.status = 'COMPLETED'
    AND d.status = 'RATIFIED'
    AND d.outcome = 'ACCEPT'
    AND d.quorum_verified = true
    AND executor.status = 'ACTIVE'
    AND coalesce(executor.review_authority, false) = false
    AND NOT 'Adjudicator' IN labels(executor)
}
RETURN
  cl.canonical_id AS accepted_claim_without_valid_promotion,
  cl.status AS status;
