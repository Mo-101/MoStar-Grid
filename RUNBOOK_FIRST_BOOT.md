# RUNBOOK FIRST BOOT

**Phase:** 4.0a Assisted Canon Ingestion Loop  
**Runtime state:** Locked until Flame authorization  
**Doctrine:** Tests before runtime. Proposal before mutation. Human approval before commit.

## Preconditions

```text
pytest -q                         -> 13 passed
.venv                             -> present and activated
Neo4j                             -> reachable before boot
Ollama                            -> optional; expected degraded state if absent
data/approval_queue/proposals.jsonl -> append-only queue path available
```

Do not boot the API if tests fail.

## Startup Order

1. Activate environment:

```bash
cd ~/MoStar/_apps/grid
source .venv/bin/activate
```

2. Confirm tests still pass:

```bash
pytest -q
```

3. Confirm Neo4j is reachable:

```bash
curl -s http://localhost:7474 >/dev/null && echo neo4j_http_ok
```

4. Boot only after explicit Flame authorization:

```bash
PYTHONPATH=. python -m uvicorn grid.api:app --host 0.0.0.0 --port 41010
```

Alternative:

```bash
./run.sh
```

## Health Checks

```bash
curl http://localhost:41010/api/health
curl http://localhost:41010/api/status
curl http://localhost:41010/api/density
curl http://localhost:41010/api/proposals
```

Expected:

```text
/api/health      -> alive; mindgraph true if Neo4j connected
/api/status      -> includes density and queue blocks
/api/density     -> returns snapshot and promotion gaps
/api/proposals   -> returns pending proposal list
```

## Expected Degraded States

```text
Ollama absent:
  dcx.connected = false
  DCX Trinity offline
  Canon proposal path still available through rule-based interpretation

Neo4j absent:
  /api/propose may still queue with limited context
  /api/approve commit fails and proposal remains approved
  No graph mutation should occur
```

## Forbidden Path Verification

```bash
curl -i -X POST http://localhost:41010/api/think \
  -H 'Content-Type: application/json' \
  -d '{"query":"test"}'

curl -i -X POST http://localhost:41010/api/learn \
  -H 'Content-Type: application/json' \
  -d '{"content":"test"}'
```

Expected:

```text
HTTP 410 Gone
```

## Approval Queue Verification

```bash
test -f data/approval_queue/proposals.jsonl && tail -n 5 data/approval_queue/proposals.jsonl
```

The file is append-only. Do not edit historical lines.

## First Ingestion Payload

Proposal:

```bash
curl -s -X POST http://localhost:41010/api/propose \
  -H 'Content-Type: application/json' \
  -d '{"canon_input":"Phase 4.0a establishes assisted canon ingestion: all graph mutations require a human-approved proposal and commit_after_seal authority."}'
```

Review the returned `proposal_id`, `interpretation`, `consistency`, `placement`, and `proposed_mutations`.

Approval:

```bash
curl -s -X POST http://localhost:41010/api/approve \
  -H 'Content-Type: application/json' \
  -d '{"proposal_id":"REPLACE_WITH_PROPOSAL_ID","approved_by":"The Flame Architect"}'
```

Expected:

```text
state = committed
memory_id present
moment_id present
```

## Rejection Sequence

```bash
curl -s -X POST http://localhost:41010/api/reject \
  -H 'Content-Type: application/json' \
  -d '{"proposal_id":"REPLACE_WITH_PROPOSAL_ID","reason":"Rejected during first boot validation."}'
```

Expected:

```text
state = rejected
rejected_reason present
no graph mutation
provenance event recorded
```

## Revision Sequence

```bash
curl -s -X POST http://localhost:41010/api/revise \
  -H 'Content-Type: application/json' \
  -d '{"proposal_id":"REPLACE_WITH_PROPOSAL_ID","corrections":"Corrected canon input."}'
```

Expected:

```text
parent proposal state = revised
new proposal state = proposed
parent_id links to original
version increments
```

## Rollback Sequence

Rollback is a counter-commit, not a direct delete.

```bash
curl -s -X POST http://localhost:41010/api/propose \
  -H 'Content-Type: application/json' \
  -d '{"canon_input":"Reversal of commit REPLACE_WITH_COMMIT_ID: rollback reason and compensating mutation request."}'
```

Then follow normal review and approval.

## Shutdown Sequence

If running foreground uvicorn, press `Ctrl+C`.

After shutdown:

```bash
curl -s http://localhost:41010/api/health || echo grid_api_stopped
```

## Post-Boot Evidence To Capture

```text
health response
status response
density snapshot
first proposal JSON
first commit JSON, if authorized
tail of data/approval_queue/proposals.jsonl
tail of data/provenance/provenance_YYYYMMDD.jsonl
```
