// LIVE GOVERNANCE RELATIONSHIP-VOCABULARY AUDIT
//
// ══════════════════════════════════════════════════════════════════════
// THIS FILE LIVES IN core/ops/audit/ ON PURPOSE.
// It uses an intentionally UNTYPED pattern -[r]-> and is therefore excluded
// from the governance relationship-type lint. Typing it would defeat it:
// the whole point is to discover relationship types nobody declared.
// ══════════════════════════════════════════════════════════════════════
//
// Source lint cannot see a `PROMOTES` created out-of-band by a Browser
// session. Only the live graph can answer that. This audit is the runtime
// counterpart to constitution/relationship_types.py.
//
// Verified 2026-08-15: (no records) — no constitutional drift. Every
// relationship touching a governance label is within the closed vocabulary.
//
// ANY ROW IS CONSTITUTIONAL DRIFT REQUIRING INVESTIGATION.
// EXPECTED: (no records)

MATCH (a)-[r]->(b)
WHERE
  any(label IN labels(a) WHERE label IN [
    'Claim', 'ReviewPanel', 'Adjudicator', 'AdjudicationCase',
    'AdjudicationDecision', 'CanonicalPromotion', 'CanonicalExecutor',
    'AuthorizationDecision', 'Testimony'
  ])
  OR
  any(label IN labels(b) WHERE label IN [
    'Claim', 'ReviewPanel', 'Adjudicator', 'AdjudicationCase',
    'AdjudicationDecision', 'CanonicalPromotion', 'CanonicalExecutor',
    'AuthorizationDecision', 'Testimony'
  ])

WITH DISTINCT type(r) AS relationship_type

WHERE NOT relationship_type IN [
  'PROMOTED', 'AUTHORIZED_BY', 'EXECUTED_BY',
  'DECIDES', 'REVIEWS', 'RESOLVES', 'ISSUED_BY',
  'ASSIGNED_TO', 'HAS_MEMBER', 'CAST_BY', 'FOR_CASE', 'FOR_CLAIM',
  'RECUSED_FROM',
  'GOVERNED_BY', 'REQUIRES', 'ADDRESSES', 'APPLIES_TO',
  'ORIGINATES_FROM', 'ATTESTED_BY',
  'SUPERSEDES', 'DISPUTES', 'CORROBORATES', 'RETRACTS',
  'DEPENDS_ON',
  'HELD_BY', 'OWED_TO', 'SATISFIES'
]

RETURN relationship_type
ORDER BY relationship_type;
