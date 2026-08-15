// GATE B1 — PROMOTION SHAPE
//
// A completed promotion into an accepted claim must promote EXACTLY ONE claim.
//
// Jurisdiction: the promotion node itself — its status and its PROMOTED
// cardinality. Says nothing about authorization, executor or topology.
//
// Catches: PENDING/FAILED promotion; promotion fanning out to two claims.
//
// EXPECTED: 0 rows

MATCH (p:CanonicalPromotion)
OPTIONAL MATCH (p)-[:PROMOTED]->(cl:Claim)

WITH p, collect(DISTINCT cl) AS claims

WHERE any(cl IN claims WHERE cl.status IN ['ACCEPTED', 'ACCEPTED_WITH_DISPUTE'])
  AND (
       p.status <> 'COMPLETED'
    OR size(claims) <> 1
  )

RETURN
  p.canonical_id AS invalid_promotion,
  p.status AS promotion_status,
  [cl IN claims | cl.canonical_id] AS promoted_claims;
