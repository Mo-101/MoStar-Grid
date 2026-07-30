// Validation pack for canonical MoStar artifact hardening.

MATCH (n)
UNWIND labels(n) AS label
WITH label, count(*) AS count
WHERE label IN [
  'MoStarMoment',
  'LifeStage',
  'Persona',
  'PersonaTrait',
  'ResonanceProfile',
  'APIEndpoint',
  'OpenAPIOperation',
  'MoStarAPIDoc',
  'SoulPrint',
  'CovenantSeal',
  'IntegrityAudit',
  'GridKnowledge',
  'Memory',
  'Domain',
  'CanonicalComponent',
  'DecisionIntelligence',
  'DecisionRun',
  'DecisionOutcome',
  'RuntimeEvent',
  'ExecutionEvent',
  'Activation',
  'GapRegisterItem',
  'RemediationTrack',
  'RemediationTask'
]
RETURN 'label_counts' AS check, label AS item, count AS value
ORDER BY item;

MATCH ()-[r]->()
WITH type(r) AS rel, count(*) AS count
WHERE rel IN [
  'HAS_PERSONA',
  'HAS_LIFESTAGE',
  'HAS_SIGNATURE',
  'SEALED_BY',
  'AUDITED_BY',
  'BINDS_LAYER',
  'HAS_MEMORY',
  'GOVERNED_BY',
  'HAS_PERSONA_TRAIT',
  'HAS_RESONANCE_PROFILE',
  'ALIGNED_WITH_CULTURE',
  'REASONS_WITH',
  'EXPRESSED_THROUGH',
  'BOUND_BY',
  'DESCRIBES',
  'EXPOSES_INTERFACE',
  'APPLIES_TO',
  'EMITS',
  'AUDITS',
  'REMEDIATED_BY',
  'HAS_REMEDIATION_TASK'
]
RETURN 'relationship_counts' AS check, rel AS item, count AS value
ORDER BY item;

SHOW CONSTRAINTS
YIELD name, type, labelsOrTypes, properties
WHERE name STARTS WITH 'canonical_'
   OR name IN ['unique_mostar_id', 'memory_id', 'identity_canonical_id']
RETURN 'constraints' AS check, name AS item, labelsOrTypes + properties AS value
ORDER BY item;

CALL () {
  MATCH (s:CovenantSeal)
  WHERE s.id IS NULL OR s.seal_id IS NULL OR s.id <> s.seal_id
  RETURN count(s) AS mismatches
}
RETURN 'property_alignment' AS check, 'CovenantSeal.id/seal_id' AS item, mismatches AS value;

CALL () {
  MATCH (a:IntegrityAudit)
  WHERE a.id IS NULL OR a.key IS NULL OR a.id <> a.key
  RETURN count(a) AS mismatches
}
RETURN 'property_alignment' AS check, 'IntegrityAudit.id/key' AS item, mismatches AS value;

CALL () {
  MATCH (e:RuntimeEvent)
  WHERE e.id IS NULL OR e.event_id IS NULL OR e.id <> e.event_id
  RETURN count(e) AS mismatches
}
RETURN 'property_alignment' AS check, 'RuntimeEvent.id/event_id' AS item, mismatches AS value;

CALL () {
  MATCH (m:MoStarMoment)
  WHERE NOT (m)-[:HAS_PERSONA]->(:Persona)
  RETURN count(m) AS missing_persona
}
RETURN 'persona_backfill' AS check, 'MoStarMoment without Persona' AS item, missing_persona AS value;
