// GATE C — STRICT TYPED RECONSTRUCTION
//
// Rebuilds the complete constitutional chain for a single claim. Every link
// is a required MATCH with an explicit relationship type.
//
// NO `OPTIONAL MATCH`. A missing constitutional link must make this audit
// return ZERO ROWS, not a row with null columns. An OPTIONAL MATCH here
// would turn "the panel never issued this decision" into a quiet null and
// still look like a successful reconstruction — the semantic false-positive
// this gate exists to prevent.
//
// Verified 2026-08-15 for claim:test:001 — returned exactly 1 coherent chain:
//   claim:test:001 / ACCEPTED / active=true
//   case:test:001 / panel:test:001
//   decision:test:001 / RATIFIED
//   promotion:test:001 / COMPLETED
//   executor:canonical:test:001
//
// EXPECTED: exactly 1 row. Zero rows = broken chain. >1 row = ambiguity
// worth investigating (duplicate cases, panels, or promotions).
//
// :param claim_id => 'claim:test:001'

MATCH (cl:Claim {canonical_id: $claim_id})

MATCH (c:AdjudicationCase)-[:REVIEWS]->(cl)
MATCH (panel:ReviewPanel)-[:ASSIGNED_TO]->(c)

MATCH (d:AdjudicationDecision)-[:DECIDES]->(c)
MATCH (d)-[:RESOLVES]->(cl)
MATCH (d)-[:ISSUED_BY]->(panel)

MATCH (promotion:CanonicalPromotion)-[:AUTHORIZED_BY]->(d)
MATCH (promotion)-[:PROMOTED]->(cl)
MATCH (promotion)-[:EXECUTED_BY]->(executor:CanonicalExecutor)

WHERE promotion.status = 'COMPLETED'
  AND d.status = 'RATIFIED'
  AND d.outcome = 'ACCEPT'
  AND d.quorum_verified = true

RETURN
  cl.canonical_id AS claim,
  cl.status AS claim_status,
  cl.active AS active,
  c.canonical_id AS case_id,
  panel.canonical_id AS panel_id,
  d.canonical_id AS decision_id,
  d.status AS decision_status,
  promotion.canonical_id AS promotion_id,
  promotion.status AS promotion_status,
  executor.canonical_id AS executor_id;
