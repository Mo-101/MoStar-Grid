// GATE B3 — EXECUTOR CARDINALITY (totality, not existence)
//
// A promotion into an accepted claim must have EXACTLY ONE constitutional
// EXECUTED_BY executor.
//
// Same reasoning as B2. An existence test is satisfied by the good executor
// and never inspects the rogue one:
//
//     CanonicalPromotion
//       ├─ EXECUTED_BY -> valid canonical executor
//       └─ EXECUTED_BY -> adjudicator / rogue executor
//
// Note `coalesce(e.review_authority, true) <> false`: the default is TRUE,
// so a missing review_authority property FAILS the gate. An executor that
// never declared its review standing is not proven separated — absence of
// the flag must not read as absence of the authority.
//
// Jurisdiction: EXECUTED_BY edges and executor standing / separation of
// duties (executor must not also be an Adjudicator).
//
// EXPECTED: 0 rows

MATCH (p:CanonicalPromotion)-[:PROMOTED]->(cl:Claim)
WHERE cl.status IN ['ACCEPTED', 'ACCEPTED_WITH_DISPUTE']

OPTIONAL MATCH (p)-[:EXECUTED_BY]->(e:CanonicalExecutor)

WITH p, cl, collect(DISTINCT e) AS executors
WITH p, cl, executors,
     CASE WHEN size(executors) = 1 THEN executors[0] ELSE null END AS e

WHERE size(executors) <> 1
   OR e IS NULL
   OR coalesce(e.status, '') <> 'ACTIVE'
   OR coalesce(e.review_authority, true) <> false
   OR coalesce('Adjudicator' IN labels(e), false) = true

RETURN
  p.canonical_id AS invalid_promotion,
  cl.canonical_id AS claim,
  size(executors) AS executor_count,
  [x IN executors | x.canonical_id] AS executor_ids;
