// Cycle 1 validation queries.

MATCH (n:SovereignCore)
WITH collect(n.entity_id) AS ids, count(n) AS total
RETURN 'sovereign_core' AS check,
  total = 2
  AND all(id IN ids WHERE id IN ['mo', 'woo'])
  AND all(required IN ['mo', 'woo'] WHERE required IN ids) AS ok,
  ids AS detail,
  total AS count;

WITH [
  'moscripts',
  'mostar_grid',
  'neo4j_mindgraph',
  'seal_chain',
  'mostar_moment_system',
  'api_gateway',
  'soul_layer',
  'mind_layer',
  'body_layer',
  'lifestage_system',
  'language_policy'
] AS required
UNWIND required AS artifact_id
OPTIONAL MATCH (a:CoreRuntime {artifact_id: artifact_id})
WITH required, collect(a.artifact_id) AS found
RETURN 'required_core_runtime' AS check,
  size([x IN required WHERE NOT x IN found]) = 0 AS ok,
  [x IN required WHERE NOT x IN found] AS detail,
  size(found) AS count;

CALL () {
  MATCH (n)
  WHERE n.attested_by IS NOT NULL
    AND n.origin_model IS NOT NULL
    AND toLower(toString(n.attested_by)) = toLower(toString(n.origin_model))
  RETURN count(n) AS self_attested_count,
    collect({
      labels: labels(n),
      id: coalesce(n.entity_id, n.agent_id, n.artifact_id, n.config_id, n.framework_id, n.run_id, n.type_name, n.actor_id, n.scope_id)
    })[0..25] AS examples
}
RETURN 'self_attestation' AS check,
  self_attested_count = 0 AS ok,
  examples AS detail,
  self_attested_count AS count;

MATCH (n {migration_run_id: 'mig-sovereign-core-consolidation-20260714'})
RETURN 'touched_nodes' AS check,
  true AS ok,
  labels(n) AS detail,
  count(*) AS count
ORDER BY count DESC;

MATCH ()-[r {migration_run_id: 'mig-sovereign-core-consolidation-20260714'}]->()
RETURN 'touched_relationships' AS check,
  true AS ok,
  type(r) AS detail,
  count(*) AS count
ORDER BY detail;

CALL db.relationshipTypes()
YIELD relationshipType
OPTIONAL MATCH (rt:RelationshipType {type_name: relationshipType})
WITH relationshipType, rt
WHERE rt IS NULL
RETURN 'live_types_missing_from_registry' AS check,
  count(relationshipType) = 0 AS ok,
  collect(relationshipType) AS detail,
  count(relationshipType) AS count;

MATCH (rt:RelationshipType)
CALL db.relationshipTypes()
YIELD relationshipType
WITH rt, collect(relationshipType) AS live_types
WHERE NOT rt.type_name IN live_types
RETURN 'registered_types_not_live' AS check,
  count(rt) = 0 AS ok,
  collect(rt.type_name) AS detail,
  count(rt) AS count;

MATCH (n)
WHERE n.verification_status = 'COMPUTED'
RETURN 'woo_seal_queue' AS check,
  true AS ok,
  labels(n) AS detail,
  count(*) AS count
ORDER BY detail;

MATCH (mo:SovereignCore {entity_id: 'mo'})
OPTIONAL MATCH (mo)-[:HAS_PROFILE]->(profile:PersonaConfig)
OPTIONAL MATCH (mo)-[:EXECUTES_THROUGH]->(runtime:CoreRuntime)
OPTIONAL MATCH (mo)-[:DEVELOPS_THROUGH]->(stage:LifeStage)
OPTIONAL MATCH (mo)-[:OPERATES_WITH_LANGUAGE_POLICY]->(policy:LanguagePolicy)
RETURN 'mo_execution_context' AS check,
  count(DISTINCT mo) = 1 AS ok,
  {
    profiles: count(DISTINCT profile),
    execution_runtimes: count(DISTINCT runtime),
    developmental_stages: count(DISTINCT stage),
    language_policies: count(DISTINCT policy)
  } AS detail,
  count(DISTINCT mo) AS count;

MATCH (agent:OperationalAgent)-[:HAS_SCOPE]->(scope:AuthScope)
RETURN 'agent_authorization' AS check,
  true AS ok,
  {
    agent_id: agent.agent_id,
    name: agent.name,
    scope_id: scope.scope_id,
    write_policy: scope.write_policy,
    allow_delete: scope.allow_delete,
    allow_unbounded_cypher: scope.allow_unbounded_cypher
  } AS detail,
  count(*) AS count
ORDER BY detail.agent_id;

MATCH (mos:CoreRuntime {artifact_id: 'moscripts'})-[r:RUNS_ON|USES_METHOD]->(framework:DecisionFramework)
RETURN 'design_vs_runtime' AS check,
  true AS ok,
  {
    relationship_type: type(r),
    framework_id: framework.framework_id,
    name: framework.name,
    implementation_status: framework.implementation_status,
    verification_status: framework.verification_status
  } AS detail,
  count(*) AS count
ORDER BY detail.implementation_status, detail.framework_id;

MATCH (legacy:LegacyIdentity)-[r:MERGED_INTO]->(core:SovereignCore)
RETURN 'legacy_identity_lineage' AS check,
  true AS ok,
  {
    legacy_identity: legacy.entity_id,
    canonical_identity: core.entity_id,
    reason: r.reason,
    migration_run_id: r.migration_run_id
  } AS detail,
  count(*) AS count
ORDER BY detail.legacy_identity;

MATCH (run:SchemaMigrationRun {run_id: 'mig-sovereign-core-consolidation-20260714'})
RETURN 'migration_receipt' AS check,
  run.status = 'COMPLETED' AND run.verification_status = 'COMPUTED' AS ok,
  {
    run_id: run.run_id,
    status: run.status,
    verification_status: run.verification_status,
    node_delta: run.node_delta,
    rel_delta: run.rel_delta,
    attested_by: run.attested_by,
    origin_model: run.origin_model
  } AS detail,
  1 AS count;
