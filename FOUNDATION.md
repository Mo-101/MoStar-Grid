# Grid — Foundation (v1)

This is the base. Everything else (Testimony, KnowledgeDomain, Seal nodes,
six-gate readiness, cross-substrate joins, provenance renames, etc.) is a
proposal that gets built **on top of** this once there's an actual reason to.
None of it is canon yet. This file is.

## Two substrates, two baselines

**Neo4j** — `schema_baseline_v1.cypher` (mirrors `ensure_schema()` in
`back/services/mindgraph/__init__.py`)

```
(:Agent {id, name, role, seal_threshold, cluster_id})
(:Memory:GridKnowledge {id, content, category, source, source_id,
    created_by, cluster_id, created_at, seal, source_type,
    verification_status, operational_trust})
(:MoStarMoment {id, talk_input, think_output, cluster_id, sealed_at, seal,
    source, created_by, source_type, verification_status,
    operational_trust})

(:MoStarMoment)-[:SEALED_FROM]->(:Memory)
```

**Postgres** — `core/ops/migrations/001_sovereign_governance.sql`

```
control_plane_resonance_state (id, component_id, current_score, level,
    contributing_events, decay_reason, threshold_crossed_at, last_computed,
    previous_level, created_at, updated_at)

graph_audit_event (id, event_type, entity_type, entity_canonical_id,
    related_canonical_id, status, payload_json, content_hash, operator_id,
    environment, source_system, created_at)
```

These two substrates do not currently link to each other. That's fine for
now — nothing in the foundation requires them to.

## What runs on the foundation today

- `MindGraph.learn()` writes `Memory:GridKnowledge` nodes.
- `MindGraph.stamp_moment()` writes `MoStarMoment` nodes.
- `MindGraph.retrieve_context()` reads via the `gridSearch` full-text index
  (fixed — see `back/services/mindgraph/__init__.py:87-126`; fails closed on
  infrastructure error instead of returning a fake empty result).
- `RuntimeEnforcementGate` gates four surfaces (`agents`, `mo_woo_nexus`,
  `decision_engine`, `moscript_registry`) against `control_plane_resonance_state`
  and writes decisions to `graph_audit_event`.

## Explicitly not in the foundation yet

Anything without a live writer: `Testimony`, `KnowledgeDomain`, `Seal` node,
`GateCondition`, `ProvenanceAttestation`, `SchemaMigrationRun`,
`event_id`/`trigger_type`/`evidence_ref` on `MoStarMoment`, six-gate readiness,
any Neo4j↔Postgres join key. These stay in the doctrine/proposal pile until
someone actually needs to write one and builds it as its own migration.

## Rule going forward

New capability → new small migration file that adds to this baseline.
Never edit history. Never delete. If a proposal never gets implemented, it
just stays a proposal — it doesn't need to be re-litigated every time.
