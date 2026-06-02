# Crossings Ledger (append-only)

Format per row: `[YYYY-MM-DD] vault:<path>@<commit> → new:<path> | scan:<pass|fail> | sealer:<id>`

<!-- Crossings are appended below this line. Do not edit prior entries. -->
[2026-05-26] original:clean-tree ? new:woo/interpreter.py | scan:pending | sealer:Cascade | note:Woo interpretation only; no governance.
[2026-05-26] original:clean-tree ? new:truth-engine/governor.py | scan:pending | sealer:Cascade | note:TruthEngine governance thresholds and veto.
[2026-05-26] original:clean-tree ? new:grid/orchestrator.py | scan:pending | sealer:Cascade | note:Grid executes only after TruthEngine pass.
[2026-05-26] original:clean-tree ? new:scripts/grid_flow.py | scan:pending | sealer:Cascade | note:Local CLI for advisory-governance-execution smoke test.
