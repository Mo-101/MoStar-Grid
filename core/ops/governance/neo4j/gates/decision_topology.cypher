// GATE B4 — DECISION TOPOLOGY
//
// The authorizing decision must have EXACTLY ONE constitutional target in
// each direction, and those targets must agree with the promoted claim.
//
// Catches the class where a decision carries one valid DECIDES plus one
// forged DECIDES — an `EXISTS { valid path }` test is satisfied by the
// valid edge and never looks at the second.
//
// Also asserts `resolved = cl`: a decision may not RESOLVE a different claim
// than the one being promoted. Existence of *some* RESOLVES edge is not
// evidence it resolves THIS claim.
//
// Jurisdiction: DECIDES / RESOLVES / ISSUED_BY cardinality, plus the
// REVIEWS and ASSIGNED_TO links that bind case, panel and claim together.
//
// EXPECTED: 0 rows

MATCH (p:CanonicalPromotion)-[:PROMOTED]->(cl:Claim)
MATCH (p)-[:AUTHORIZED_BY]->(d:AdjudicationDecision)
WHERE cl.status IN ['ACCEPTED', 'ACCEPTED_WITH_DISPUTE']

OPTIONAL MATCH (d)-[:DECIDES]->(caseNode:AdjudicationCase)
WITH p, cl, d, collect(DISTINCT caseNode) AS cases

OPTIONAL MATCH (d)-[:RESOLVES]->(resolvedNode:Claim)
WITH p, cl, d, cases, collect(DISTINCT resolvedNode) AS resolvedClaims

OPTIONAL MATCH (d)-[:ISSUED_BY]->(panelNode:ReviewPanel)
WITH p, cl, d, cases, resolvedClaims, collect(DISTINCT panelNode) AS panels

WITH p, cl, d, cases, resolvedClaims, panels,
     CASE WHEN size(cases) = 1 THEN cases[0] ELSE null END AS c,
     CASE WHEN size(resolvedClaims) = 1 THEN resolvedClaims[0] ELSE null END AS resolved,
     CASE WHEN size(panels) = 1 THEN panels[0] ELSE null END AS panel

WHERE size(cases) <> 1
   OR size(resolvedClaims) <> 1
   OR size(panels) <> 1
   OR resolved IS NULL
   OR resolved <> cl
   OR NOT EXISTS { MATCH (c)-[:REVIEWS]->(cl) }
   OR NOT EXISTS { MATCH (panel)-[:ASSIGNED_TO]->(c) }

RETURN
  p.canonical_id AS invalid_promotion,
  d.canonical_id AS decision,
  cl.canonical_id AS claim,
  [x IN cases | x.canonical_id] AS cases,
  [x IN resolvedClaims | x.canonical_id] AS resolved_claims,
  [x IN panels | x.canonical_id] AS panels;
