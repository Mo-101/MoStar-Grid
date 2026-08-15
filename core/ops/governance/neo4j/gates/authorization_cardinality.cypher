// GATE B2 — AUTHORIZATION CARDINALITY (totality, not existence)
//
// A promotion into an accepted claim must have EXACTLY ONE constitutional
// AUTHORIZED_BY decision.
//
// ══════════════════════════════════════════════════════════════════════
// WHY CARDINALITY AND NOT `NOT EXISTS { valid path }`
// ══════════════════════════════════════════════════════════════════════
// The original absence-of-bad gate asked "does a valid authorization path
// exist?". That is satisfied by ONE valid edge — so this passes it:
//
//     CanonicalPromotion
//       ├─ AUTHORIZED_BY -> valid ratified decision
//       └─ AUTHORIZED_BY -> forged decision
//
// The valid edge makes NOT EXISTS{...} false and the forged edge is never
// examined. "At least one good path" is not "only good paths". This gate
// counts instead: authorization_count = 2 fails regardless of how perfect
// one of them is.
//
// Jurisdiction: AUTHORIZED_BY edges and the authorizing decision's own
// status/outcome/quorum flags. Decision TOPOLOGY is gate B4's job.
//
// EXPECTED: 0 rows

MATCH (p:CanonicalPromotion)-[:PROMOTED]->(cl:Claim)
WHERE cl.status IN ['ACCEPTED', 'ACCEPTED_WITH_DISPUTE']

OPTIONAL MATCH (p)-[:AUTHORIZED_BY]->(d:AdjudicationDecision)

WITH p, cl, collect(DISTINCT d) AS decisions
WITH p, cl, decisions,
     CASE WHEN size(decisions) = 1 THEN decisions[0] ELSE null END AS d

WHERE size(decisions) <> 1
   OR d IS NULL
   OR coalesce(d.status, '') <> 'RATIFIED'
   OR coalesce(d.outcome, '') <> 'ACCEPT'
   OR coalesce(d.quorum_verified, false) <> true

RETURN
  p.canonical_id AS invalid_promotion,
  cl.canonical_id AS claim,
  size(decisions) AS authorization_count,
  [x IN decisions | x.canonical_id] AS decision_ids;
