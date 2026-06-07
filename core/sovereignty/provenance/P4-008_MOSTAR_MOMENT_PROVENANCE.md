# P4-008 MoStarMoment Provenance Alignment

**Date:** 2026-06-07
**Status:** CLOSED - Option B runtime-only API label applied
**Scope:** `MoStarMoment` provenance fields, static imports, and `/api/provenance`

## Verified State

Live Neo4j inspection on 2026-06-07 found:

```text
MoStarMoment total nodes:                 13,865
nodes with source_type:                   1
nodes with verification_status:           1
nodes with operational_trust:             1
nodes with seal:                          1
nodes with source:                        1
nodes with created_by:                    1
nodes with legacy provenance property:    0
```

Missing-node label distribution:

```text
["MoStarMoment", "Grid"]            13,832
["MoStarMoment", "StartupReport"]       26
["MoStarMoment", "WooUtterance"]         5
["MoStarMoment", "AgentUtterance"]       1
```

Label-aware dry-run preview:

```text
13,864 missing-context nodes -> runtime_generated / synthetic / simulation
0 missing-context nodes      -> imported_archive / unverified / reference
```

The Python write path already supports provenance classification:

```text
source_type
verification_status
operational_trust
seal
source
created_by
```

Therefore P4-008 is not a schema invention. It is a classification,
backfill, and API alignment task.

## Backfill Result

The v2 label-aware backfill was applied on 2026-06-07.

Before-apply evidence snapshot:

```text
core/sovereignty/provenance/snapshots/p4_008_before_apply_20260607.json
```

Apply result:

```text
nodes_backfilled: 13,864
```

After counts:

```text
total:                    13,865
with_source_type:         13,865
with_verification_status: 13,865
with_operational_trust:   13,865
with_seal:                13,865
with_source:              13,865
with_created_by:          13,865
missing_required_context: 0
```

After distribution:

```text
runtime_generated / synthetic / simulation / UNSEALED:P4-008-CONSERVATIVE-BACKFILL:RUNTIME-GENERATED  13,864
human_attested / verified / operational / Operational                                                   1
```

This backfill made provenance explicit. It did not promote the 13,864 runtime
generated moments to canon or operational truth.

## Current Gap

`/api/provenance` currently reports the in-memory orchestrator provenance
log. It can return zero even when Neo4j contains many `MoStarMoment` nodes.

That endpoint must not be treated as proof of graph provenance until it reads
from the persistent graph or clearly labels itself as runtime-memory-only.

## Classification Rules

Every `MoStarMoment` must carry these fields before it can be considered
operationally trustworthy:

```text
source_type
verification_status
operational_trust
seal
source
created_by
```

Allowed `source_type` values:

```text
human_attested
imported_archive
runtime_generated
seeded_demo
ai_generated
live_api
```

Allowed `verification_status` values:

```text
verified
unverified
synthetic
disputed
```

Allowed `operational_trust` values:

```text
operational
reference
simulation
design
```

## Trust Defaults

Backfill must be conservative.

```text
missing provenance fields      -> not operational
static archive moments         -> imported_archive / unverified / reference
runtime Grid events            -> runtime_generated / synthetic / simulation
startup roll-call utterances   -> runtime_generated / synthetic / simulation
live service health moments    -> live_api / verified only if source checked
human-sealed canon moments     -> human_attested / verified / operational
AI-only interpretations        -> ai_generated / unverified / reference
```

No imported or generated moment may be promoted to `operational` without a
separate human seal.

## Backfill Requirements

The backfill must:

1. Preserve every existing node and raw field.
2. Only add missing classification fields.
3. Never overwrite an existing provenance field without a reviewed migration.
4. Record the migration date and migration tool name.
5. Produce before/after counts.

Backfill tool:

```text
scripts/provenance/p4_008_mostar_moment_backfill.py
```

The script is label-aware. Runtime-shaped labels and fields are classified as
`runtime_generated / synthetic / simulation`; unknown legacy/archive labels are
classified as `imported_archive / unverified / reference`.

Required before/after query:

```cypher
MATCH (m:MoStarMoment)
RETURN
  count(m) AS total,
  count(m.source_type) AS with_source_type,
  count(m.verification_status) AS with_verification_status,
  count(m.operational_trust) AS with_operational_trust,
  count(m.seal) AS with_seal,
  count(m.source) AS with_source,
  count(m.created_by) AS with_created_by;
```

## API Alignment

`/api/provenance` was changed using Option B.

Decision:

```text
/api/provenance alignment: Option B
endpoint scope: runtime-memory-only
store: orchestrator-memory
persistent_graph_backed: false
p4_008_status: backfill-complete-api-runtime-labeled
graph-backed provenance endpoint: deferred to P4-010
```

The endpoint now explicitly warns that it reflects volatile in-memory
orchestrator provenance only and is not proof of persistent `MoStarMoment`
graph provenance.

Original alignment options:

```text
Option A: graph-backed provenance endpoint
  reads `MoStarMoment` and provenance-chain nodes from Neo4j

Option B: runtime-only endpoint
  keeps current behavior but renames or labels response as volatile runtime log
```

The preferred Phase 4 direction is Option A.

## Seal Condition

P4-008 is complete only when:

```text
all MoStarMoment nodes have required provenance fields
/api/provenance reports persistent provenance or clearly declares runtime-only scope
missing context cannot be reported as verified
before/after migration counts are preserved in the provenance ledger
```

Current seal status:

```text
MoStarMoment required-field backfill: complete
/api/provenance alignment: Option B runtime-memory-only label complete
missing_required_context: 0
before/after counts: recorded
P4-008 final closure: closed
```
