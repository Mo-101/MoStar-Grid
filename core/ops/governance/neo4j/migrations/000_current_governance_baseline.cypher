// ═══════════════════════════════════════════════════════════════════════
// 000_current_governance_baseline.cypher
// ═══════════════════════════════════════════════════════════════════════
//
// PROVENANCE — READ THIS FIRST
//
//   This file is a RECONCILIATION of a constitution that was already applied
//   to the live Neo4j database out-of-band. It is NOT a claim that Git
//   created these objects.
//
//   Discovered 2026-08-15: the live graph held 208 labels and 140
//   relationship types, including the full adjudication constitution
//   (Claim, ReviewPanel, Adjudicator, AdjudicationCase, AdjudicationDecision,
//   CanonicalPromotion, CanonicalExecutor, AuthorizationDecision, Testimony)
//   with 13 uniqueness constraints and 19 indexes — while
//   core/ops/migrations/ contained only 001_sovereign_governance.sql
//   (Postgres). Production schema was ahead of source control with no
//   versioned origin.
//
//   Everything below was read back from the live database via SHOW
//   CONSTRAINTS / SHOW INDEXES on 2026-08-15 and rewritten in idempotent
//   form. Applying it to the current database is a no-op; applying it to a
//   fresh database reproduces the constitutional structure.
//
// SCOPE
//   Contains:     constraints, indexes, structural setup.
//   Contains NOT: instance data, synthetic fixtures (claim:test:001 et al),
//                 votes, decisions, promotions, credentials, dumped rows.
//
//   Synthetic smoke-test state still resident in the live graph is handled
//   separately — it must be tagged and purged through the maintenance
//   identity, NOT from the Browser principal. See gates/synthetic_isolation.cypher
//
// SAFETY
//   Every statement is IF NOT EXISTS. Re-running is safe and non-destructive.
// ═══════════════════════════════════════════════════════════════════════

// ── Identity constraints ───────────────────────────────────────────────
// Every constitutional node is identified by canonical_id. These uniqueness
// constraints are what make the promotion gates' lookups NodeUniqueIndexSeek
// rather than label scans.

CREATE CONSTRAINT claim_canonical_id IF NOT EXISTS
FOR (n:Claim) REQUIRE n.canonical_id IS UNIQUE;

CREATE CONSTRAINT review_panel_canonical_id IF NOT EXISTS
FOR (n:ReviewPanel) REQUIRE n.canonical_id IS UNIQUE;

CREATE CONSTRAINT adjudicator_canonical_id IF NOT EXISTS
FOR (n:Adjudicator) REQUIRE n.canonical_id IS UNIQUE;

CREATE CONSTRAINT adjudication_case_canonical_id IF NOT EXISTS
FOR (n:AdjudicationCase) REQUIRE n.canonical_id IS UNIQUE;

CREATE CONSTRAINT adjudication_decision_canonical_id IF NOT EXISTS
FOR (n:AdjudicationDecision) REQUIRE n.canonical_id IS UNIQUE;

CREATE CONSTRAINT adjudication_vote_canonical_id IF NOT EXISTS
FOR (n:AdjudicationVote) REQUIRE n.canonical_id IS UNIQUE;

CREATE CONSTRAINT canonical_promotion_canonical_id IF NOT EXISTS
FOR (n:CanonicalPromotion) REQUIRE n.canonical_id IS UNIQUE;

CREATE CONSTRAINT canonical_executor_canonical_id IF NOT EXISTS
FOR (n:CanonicalExecutor) REQUIRE n.canonical_id IS UNIQUE;

CREATE CONSTRAINT authorization_decision_canonical_id IF NOT EXISTS
FOR (n:AuthorizationDecision) REQUIRE n.canonical_id IS UNIQUE;

CREATE CONSTRAINT testimony_canonical_id IF NOT EXISTS
FOR (n:Testimony) REQUIRE n.canonical_id IS UNIQUE;

CREATE CONSTRAINT attestor_canonical_id IF NOT EXISTS
FOR (n:Attestor) REQUIRE n.canonical_id IS UNIQUE;

CREATE CONSTRAINT institution_canonical_id IF NOT EXISTS
FOR (n:Institution) REQUIRE n.canonical_id IS UNIQUE;

CREATE CONSTRAINT knowledge_boundary_canonical_id IF NOT EXISTS
FOR (n:KnowledgeBoundary) REQUIRE n.canonical_id IS UNIQUE;

// ── Query-path indexes ─────────────────────────────────────────────────
// Non-constraint-backed indexes observed live. Constraint-backed RANGE
// indexes are created implicitly by the constraints above and are NOT
// redeclared here.

CREATE INDEX claim_status IF NOT EXISTS
FOR (n:Claim) ON (n.status);

CREATE INDEX claim_domain IF NOT EXISTS
FOR (n:Claim) ON (n.domain);

CREATE INDEX adjudication_case_status IF NOT EXISTS
FOR (n:AdjudicationCase) ON (n.status);

CREATE INDEX authorization_dimension_decision IF NOT EXISTS
FOR (n:AuthorizationDecision) ON (n.dimension, n.decision);

CREATE INDEX boundary_visibility IF NOT EXISTS
FOR (n:KnowledgeBoundary) ON (n.visibility);

CREATE INDEX testimony_recording_state IF NOT EXISTS
FOR (n:Testimony) ON (n.recording_state);

// ═══════════════════════════════════════════════════════════════════════
// SEPARATION OF DUTIES — enforced by gates, not yet by the database
// ═══════════════════════════════════════════════════════════════════════
//
//   executor.review_authority = false
//   NOT 'Adjudicator' IN labels(executor)
//
// These are currently asserted only inside the promotion gates. Neo4j
// Community cannot express them as constraints, and RBAC role separation
// (browser_reader / adjudication_writer / canonical_executor /
// authorization_issuer / authorization_verifier / governance_migrator) is
// not yet in place. Until it is, separation of powers is LOGICAL ONLY —
// any principal with write access can bypass it.
//
// Tracking: steps 9-10 of the governance execution order.
// ═══════════════════════════════════════════════════════════════════════
