// GATE D — SYNTHETIC ISOLATION (production release blocker)
//
// ══════════════════════════════════════════════════════════════════════
// CRITICAL: WHY THIS QUERY CHECKS TWO THINGS
// ══════════════════════════════════════════════════════════════════════
//
// The obvious form of this gate is:
//
//     MATCH (n {synthetic: true}) RETURN n
//
// On 2026-08-15 that returned zero rows — and it was MEANINGLESS. Neo4j
// emitted warning 01N52: "The property `synthetic` does not exist in
// database `neo4j`." The property had never been written to any node.
//
// So the query reported "production ready" against a graph whose ONLY
// governance content was synthetic. Zero rows meant "nobody has ever
// tagged anything", not "nothing synthetic is present". That is precisely
// a semantic false-positive: an assertion that is trivially satisfiable
// because its subject does not exist.
//
// Until the tagging write has run under the maintenance identity, the real
// witness of synthetic state is the ':test:' canonical_id convention.
// This gate therefore checks BOTH forms, and must keep doing so through
// the transition.
//
// EXPECTED BEFORE PRODUCTION INTAKE: 0 rows
// CURRENT (2026-08-15): 9 nodes match via ':test:' — 1 Claim, 1 ReviewPanel,
//   2 Adjudicator, 2 AdjudicationCase, 1 AdjudicationDecision,
//   1 CanonicalPromotion, 1 CanonicalExecutor. Tagged count: 0.

MATCH (n)
WHERE n.synthetic = true
   OR n.canonical_id CONTAINS ':test:'
RETURN
  labels(n) AS labels,
  n.canonical_id AS synthetic_object,
  coalesce(n.synthetic, false) AS tagged,
  n.synthetic_suite AS suite
ORDER BY synthetic_object;


// ── Narrower blocker, meaningful once real data exists ─────────────────
// Real canon must never depend on a synthetic promotion.
//
// NOTE the `coalesce`: writing `cl.synthetic <> true` would silently drop
// every node where the property is absent (null <> true yields null, not
// true), which is every real claim today. That comparison would make this
// gate vacuous for exactly the population it is meant to protect.
//
// EXPECTED: 0 rows

// MATCH (cl:Claim)
// WHERE coalesce(cl.synthetic, false) = false
//   AND cl.status IN ['ACCEPTED', 'ACCEPTED_WITH_DISPUTE']
//   AND EXISTS {
//     MATCH (promotion:CanonicalPromotion)-[:PROMOTED]->(cl)
//     WHERE promotion.synthetic = true
//   }
// RETURN cl.canonical_id AS real_claim_promoted_by_synthetic_evidence;
