// Canonical MoStar artifact graph hardening.
// Aligns id/key/event_id/seal_id fields used by older graph data with the
// current API contract, backfills absent canonical anchors, and creates
// uniqueness constraints for the first-class artifact model.

// ---- Property-name normalization ----
MATCH (s:CovenantSeal)
WHERE s.id IS NULL AND s.seal_id IS NOT NULL
SET s.id = s.seal_id;

MATCH (s:CovenantSeal)
WHERE s.id IS NULL AND s.seal_id IS NULL
WITH s, 'seal_' + randomUUID() AS generated_id
SET s.id = generated_id,
    s.seal_id = generated_id;

MATCH (s:CovenantSeal)
WHERE s.seal_id IS NULL AND s.id IS NOT NULL
SET s.seal_id = s.id;

MATCH (a:IntegrityAudit)
WHERE a.id IS NULL AND a.key IS NOT NULL
SET a.id = a.key;

MATCH (a:IntegrityAudit)
WHERE a.id IS NULL AND a.key IS NULL
WITH a, 'audit_' + randomUUID() AS generated_id
SET a.id = generated_id,
    a.key = generated_id;

MATCH (a:IntegrityAudit)
WHERE a.key IS NULL AND a.id IS NOT NULL
SET a.key = a.id;

MATCH (e:RuntimeEvent)
WHERE e.id IS NULL AND e.event_id IS NOT NULL
SET e.id = e.event_id;

MATCH (e:RuntimeEvent)
WHERE e.id IS NULL AND e.event_id IS NULL
WITH e, 'runtime_' + randomUUID() AS generated_id
SET e.id = generated_id,
    e.event_id = generated_id;

MATCH (e:RuntimeEvent)
WHERE e.event_id IS NULL AND e.id IS NOT NULL
SET e.event_id = e.id;

MATCH (e:RuntimeEvent)
WHERE e.id IS NOT NULL AND e.event_id IS NOT NULL AND e.id <> e.event_id
SET e.id = e.event_id;

MATCH (e:ExecutionEvent)
WHERE e.id IS NULL AND e.execution_id IS NOT NULL
SET e.id = e.execution_id;

MATCH (e:ExecutionEvent)
WHERE e.execution_id IS NULL AND e.id IS NOT NULL
SET e.execution_id = e.id;

MATCH (e:ExecutionEvent)
WHERE e.id IS NOT NULL AND e.execution_id IS NOT NULL AND e.id <> e.execution_id
SET e.id = e.execution_id;

MATCH (ls:LifeStage)
WHERE ls.id IS NULL AND ls.key IS NOT NULL
SET ls.id = ls.key;

MATCH (ls:LifeStage)
WHERE ls.key IS NULL AND ls.id IS NOT NULL
SET ls.key = ls.id;

MATCH (api:APIEndpoint)
WHERE api.id IS NULL AND api.endpoint_id IS NOT NULL
SET api.id = api.endpoint_id;

MATCH (api:APIEndpoint)
WHERE api.endpoint_id IS NULL AND api.id IS NOT NULL
SET api.endpoint_id = api.id;

MATCH (op:OpenAPIOperation)
WHERE op.id IS NULL AND op.operation_id IS NOT NULL
SET op.id = op.operation_id;

MATCH (op:OpenAPIOperation)
WHERE op.operation_id IS NULL AND op.id IS NOT NULL
SET op.operation_id = op.id;

MATCH (c:CanonicalComponent)
WHERE c.id IS NULL AND c.canonical_id IS NOT NULL
SET c.id = c.canonical_id;

MATCH (c:CanonicalComponent)
WHERE c.canonical_id IS NULL AND c.id IS NOT NULL
SET c.canonical_id = c.id;

MATCH (sp:SoulPrint)
WHERE sp.id IS NULL AND sp.key IS NOT NULL
SET sp.id = sp.key;

MATCH (sp:SoulPrint)
WHERE sp.key IS NULL AND sp.id IS NOT NULL
SET sp.key = sp.id;

MATCH (g:GridKnowledge)
WHERE g.id IS NULL AND g.canonical_id IS NOT NULL
SET g.id = g.canonical_id;

MATCH (g:GridKnowledge)
WHERE g.canonical_id IS NULL AND g.id IS NOT NULL
SET g.canonical_id = g.id;

MATCH (d:DecisionRun)
WHERE d.id IS NULL AND d.run_id IS NOT NULL
SET d.id = d.run_id;

MATCH (d:DecisionRun)
WHERE d.run_id IS NULL AND d.id IS NOT NULL
SET d.run_id = d.id;

MATCH (d:DecisionOutcome)
WHERE d.id IS NULL AND d.outcome_id IS NOT NULL
SET d.id = d.outcome_id;

MATCH (d:DecisionOutcome)
WHERE d.outcome_id IS NULL AND d.id IS NOT NULL
SET d.outcome_id = d.id;

MATCH (a:Activation)
WHERE a.id IS NULL AND a.key IS NOT NULL
SET a.id = a.key;

MATCH (a:Activation)
WHERE a.key IS NULL AND a.id IS NOT NULL
SET a.key = a.id;

// ---- Persona backfill ----
MATCH (t:PersonaTrait)
WITH collect(t) AS traits
MERGE (p:Persona {id: 'default-persona'})
ON CREATE SET p.name = 'Default Persona',
              p.active = false,
              p.created_at = datetime(),
              p.source = 'canonical-hardening-migration'
WITH p, traits
UNWIND traits AS trait
MERGE (p)-[:HAS_PERSONA_TRAIT]->(trait);

MATCH (rp:ResonanceProfile)
WITH collect(rp) AS profiles
MERGE (p:Persona {id: 'default-persona'})
WITH p, profiles
UNWIND profiles AS profile
MERGE (p)-[:HAS_RESONANCE_PROFILE]->(profile);

MATCH (m:MoStarMoment)
WHERE NOT (m)-[:HAS_PERSONA]->(:Persona)
MATCH (p:Persona {id: 'default-persona'})
MERGE (m)-[:HAS_PERSONA]->(p);

// ---- Canonical uniqueness constraints ----
DROP INDEX endpoint_id_idx IF EXISTS;
DROP INDEX index_ff4371d4 IF EXISTS;

CREATE CONSTRAINT unique_mostar_id IF NOT EXISTS
FOR (m:MoStarMoment)
REQUIRE m.id IS UNIQUE;

CREATE CONSTRAINT canonical_lifestage_key IF NOT EXISTS
FOR (ls:LifeStage)
REQUIRE ls.key IS UNIQUE;

CREATE CONSTRAINT canonical_persona_id IF NOT EXISTS
FOR (p:Persona)
REQUIRE p.id IS UNIQUE;

CREATE CONSTRAINT canonical_persona_trait_key IF NOT EXISTS
FOR (t:PersonaTrait)
REQUIRE t.key IS UNIQUE;

CREATE CONSTRAINT canonical_resonance_profile_id IF NOT EXISTS
FOR (r:ResonanceProfile)
REQUIRE r.id IS UNIQUE;

CREATE CONSTRAINT canonical_api_endpoint_id IF NOT EXISTS
FOR (e:APIEndpoint)
REQUIRE e.endpoint_id IS UNIQUE;

CREATE CONSTRAINT canonical_openapi_operation_id IF NOT EXISTS
FOR (o:OpenAPIOperation)
REQUIRE o.operation_id IS UNIQUE;

CREATE CONSTRAINT canonical_mostar_api_doc_id IF NOT EXISTS
FOR (d:MoStarAPIDoc)
REQUIRE d.id IS UNIQUE;

CREATE CONSTRAINT canonical_covenant_seal_id IF NOT EXISTS
FOR (s:CovenantSeal)
REQUIRE s.id IS UNIQUE;

CREATE CONSTRAINT canonical_integrity_audit_id IF NOT EXISTS
FOR (a:IntegrityAudit)
REQUIRE a.id IS UNIQUE;

CREATE CONSTRAINT canonical_grid_knowledge_id IF NOT EXISTS
FOR (g:GridKnowledge)
REQUIRE g.id IS UNIQUE;

CREATE CONSTRAINT memory_id IF NOT EXISTS
FOR (m:Memory)
REQUIRE m.id IS UNIQUE;

CREATE CONSTRAINT identity_canonical_id IF NOT EXISTS
FOR (c:CanonicalComponent)
REQUIRE c.canonical_id IS UNIQUE;

CREATE CONSTRAINT canonical_decision_intelligence_id IF NOT EXISTS
FOR (d:DecisionIntelligence)
REQUIRE d.id IS UNIQUE;

CREATE CONSTRAINT canonical_decision_run_id IF NOT EXISTS
FOR (d:DecisionRun)
REQUIRE d.id IS UNIQUE;

CREATE CONSTRAINT canonical_decision_outcome_id IF NOT EXISTS
FOR (d:DecisionOutcome)
REQUIRE d.id IS UNIQUE;

CREATE CONSTRAINT canonical_runtime_event_id IF NOT EXISTS
FOR (e:RuntimeEvent)
REQUIRE e.id IS UNIQUE;

CREATE CONSTRAINT canonical_execution_event_id IF NOT EXISTS
FOR (e:ExecutionEvent)
REQUIRE e.id IS UNIQUE;

CREATE CONSTRAINT canonical_activation_id IF NOT EXISTS
FOR (a:Activation)
REQUIRE a.id IS UNIQUE;

CREATE CONSTRAINT canonical_gap_register_item_id IF NOT EXISTS
FOR (g:GapRegisterItem)
REQUIRE g.gap_id IS UNIQUE;

CREATE CONSTRAINT canonical_remediation_track_name IF NOT EXISTS
FOR (r:RemediationTrack)
REQUIRE r.name IS UNIQUE;

CREATE CONSTRAINT canonical_remediation_task_key IF NOT EXISTS
FOR (t:RemediationTask)
REQUIRE (t.gap_id, t.title) IS UNIQUE;

// ---- Migration audit event ----
MERGE (evt:RuntimeEvent {event_id: 'canonical_artifact_hardening_v1'})
SET evt.id = 'canonical_artifact_hardening_v1',
    evt.type = 'CANONICAL_ARTIFACT_HARDENING_APPLIED',
    evt.created_at = coalesce(evt.created_at, toString(datetime())),
    evt.cluster_id = coalesce(evt.cluster_id, 'nairobi-alpha');
