# Crossings Ledger (append-only)

Format per row: `[YYYY-MM-DD] vault:<path>@<commit> → new:<path> | scan:<pass|fail> | sealer:<id>`

<!-- Crossings are appended below this line. Do not edit prior entries. -->
[2026-05-26] original:clean-tree ? new:woo/interpreter.py | scan:pending | sealer:Cascade | note:Woo interpretation only; no governance.
[2026-05-26] original:clean-tree ? new:truth-engine/governor.py | scan:pending | sealer:Cascade | note:TruthEngine governance thresholds and veto.
[2026-05-26] original:clean-tree ? new:grid/orchestrator.py | scan:pending | sealer:Cascade | note:Grid executes only after TruthEngine pass.
[2026-05-26] original:clean-tree ? new:scripts/grid_flow.py | scan:pending | sealer:Cascade | note:Local CLI for advisory-governance-execution smoke test.
[2026-06-07] graph:MoStarMoment provenance dry-run -> scripts/provenance/p4_008_mostar_moment_backfill.py | scan:dry-run-pass | sealer:Codex | note:P4-008 v2 label-aware preview preserved; 13,864 missing-context nodes classify as runtime_generated/synthetic/simulation; no mutation performed.
[2026-06-07] graph:MoStarMoment required provenance backfill -> Neo4j | scan:apply-pass | sealer:Codex | note:P4-008 v2 applied; 13,864 nodes backfilled; missing_required_context=0; /api/provenance alignment still pending.
[2026-06-07] api:/api/provenance alignment -> back/services/grid/api.py | scan:option-b-label-applied | sealer:Codex | note:Endpoint explicitly declares runtime-memory-only scope; persistent graph provenance backfilled; graph-backed provenance deferred to P4-010; P4-008 closed.
