// GATE B — ABSENCE-OF-BAD (negative witness)
//
//   "Every promotion into an accepted claim is itself valid."
//
// Verified 2026-08-15: (no records) — evaluated over ONE synthetic promotion.
//
// WHY THIS EXISTS SEPARATELY FROM GATE A
//   Gate A is satisfied by the existence of one valid path. It stays green
//   even if a forged CanonicalPromotion is ALSO attached to the same claim.
//   Gate B quantifies the other way: it starts from every promotion and
//   demands each one be constitutionally complete.
//
//   A: at least one valid route exists
//   B: no invalid route exists
//
//   The decisive fixture is "one valid + one forged promotion": A must PASS
//   while B must FAIL. If both pass on that fixture, the pair is not doing
//   distinct work and B is miswritten.
//
// EXPECTED: (no records)

MATCH (promotion:CanonicalPromotion)-[:PROMOTED]->(cl:Claim)
WHERE cl.status IN ['ACCEPTED', 'ACCEPTED_WITH_DISPUTE']
AND NOT EXISTS {
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
  promotion.canonical_id AS invalid_promotion,
  cl.canonical_id AS affected_claim,
  promotion.status AS promotion_status;
