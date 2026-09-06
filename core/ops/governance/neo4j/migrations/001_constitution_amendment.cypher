// Constitution amendment migration for GRID_MIND_CONSTITUTION.md
// Binds the new SHA-256 digest to Constitution, Provenance, and Attestation nodes.
// MERGE-only: no DELETE, DETACH DELETE, or REMOVE operations are present.

MERGE (c:Constitution {constitution_hash: 'e797c19cbb7ede42fe4a17fde301dcc1afb05b785ca6a5b8feee27a417b9ad87'})
SET c.id = coalesce(c.id, randomUUID()),
    c.previous_hash = '02913f525e263737d87a8625bdc97efc940ffcfb6e6e58f09cb5cbbe573be0b2',
    c.lineage = 'GENESIS',
    c.ratified_at = coalesce(c.ratified_at, timestamp())

WITH c
MERGE (p:Provenance {constitution_hash: c.constitution_hash})
SET p.id = coalesce(p.id, randomUUID()),
    p.source = 'core/ops/governance/GRID_MIND_CONSTITUTION.md',
    p.origin = 'amendment',
    p.created_at = coalesce(p.created_at, timestamp())

WITH c, p
MERGE (a:Attestation {constitution_hash: c.constitution_hash})
SET a.id = coalesce(a.id, randomUUID()),
    a.attested_by = 'Devin',
    a.origin_model = 'none',
    a.attested_at = coalesce(a.attested_at, timestamp())

WITH c, p, a
MERGE (c)-[:ORIGINATES_FROM]->(p)
MERGE (p)-[:ATTESTED_BY]->(a);
