// =============================================================================
// GRID — Neo4j Base Schema (v1 Foundation)
// =============================================================================
// This is the ONLY schema treated as canon right now. It contains exactly what
// is LIVE-CONFIRMED in code — nothing proposed, nothing aspirational.
//
// Source of truth: back/services/mindgraph/__init__.py (ensure_schema, learn,
// stamp_moment, get_agents). This file is the same statements, kept as a
// standalone, reviewable artifact and a stable base for future migrations.
//
// Everything else discussed so far (Testimony, KnowledgeDomain, Seal,
// GateCondition, ProvenanceAttestation, SchemaMigrationRun, event_id/
// trigger_type/evidence_ref MoStarMoment fields, etc.) is PROPOSED, not part
// of this baseline. Add it later as its own additive migration once a real
// writer exists — do not fold it in here.
//
// Rule for every future change: ADD, never DELETE/DETACH DELETE. New
// properties/labels/relationships get their own migration file that states
// what it adds and why.
// =============================================================================

// ── Node labels in this baseline ────────────────────────────────────────────
// (:Agent {id, name, role, seal_threshold, cluster_id, ...})
// (:Memory:GridKnowledge {id, content, category, source, source_id,
//     created_by, cluster_id, created_at, seal, source_type,
//     verification_status, operational_trust, metadata?})
// (:MoStarMoment {id, talk_input, think_output, cluster_id, sealed_at, seal,
//     source, created_by, source_type, verification_status,
//     operational_trust})
//
// ── Relationships in this baseline ──────────────────────────────────────────
// (:MoStarMoment)-[:SEALED_FROM]->(:Memory)

// ── Constraints ──────────────────────────────────────────────────────────────
CREATE CONSTRAINT agent_id IF NOT EXISTS
  FOR (a:Agent) REQUIRE a.id IS UNIQUE;

CREATE CONSTRAINT memory_id IF NOT EXISTS
  FOR (m:Memory) REQUIRE m.id IS UNIQUE;

CREATE CONSTRAINT moment_id IF NOT EXISTS
  FOR (m:MoStarMoment) REQUIRE m.id IS UNIQUE;

// ── Indexes ──────────────────────────────────────────────────────────────────
CREATE INDEX cluster_id IF NOT EXISTS
  FOR (n:GridKnowledge) ON (n.cluster_id);

CREATE INDEX memory_category IF NOT EXISTS
  FOR (m:Memory) ON (m.category);

CREATE INDEX moment_sealed IF NOT EXISTS
  FOR (m:MoStarMoment) ON (m.sealed_at);

// ── Full-text search (the index retrieve_context() depends on) ──────────────
CREATE FULLTEXT INDEX gridSearch IF NOT EXISTS
  FOR (n:Memory|Agent|MoStarMoment|GridKnowledge)
  ON EACH [n.content, n.name, n.category, n.id];
