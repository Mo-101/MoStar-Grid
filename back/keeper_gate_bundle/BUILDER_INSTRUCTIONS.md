# KEEPER GATE BUNDLE — BUILDER INSTRUCTIONS

**Authority:** The Flame Architect. These instructions are not suggestions.
**Audit:** Claude (this bundle is self-tested — `tests/selftest.py`, 15/15).
**Why this exists:** On 2026-06-11 a builder executed `DETACH DELETE` against the
keeper of truth behind a comment that said `# Clear test graph`. 95,115 nodes
were restored from export. This bundle ensures that day cannot happen twice.

---

## ORDER OF OPERATIONS — DO NOT REORDER

### Step 0 — Read everything. Touch nothing.
Read every file in this bundle before executing anything. Then run:
```bash
python3 tests/selftest.py        # must print ALL PASS (15/15)
```
If it does not pass on the target machine, STOP and report. Do not "fix" the tests.

### Step 1 — Environment file (Flame's hand, not yours)
```bash
cp conf/keeper_gate.env.example /home/idona/.neo4j_keeper_gate.env
```
**Flame personally** sets `NEO4J_PASSWORD` and `FLAME_SEAL`, then:
```bash
chmod 600 /home/idona/.neo4j_keeper_gate.env
```
You never read, echo, log, or transmit `FLAME_SEAL`. It appears in no code,
no commit, no console output, no agent context.

### Step 2 — GOLDEN DUMP. Before anything else touches the graph.
```bash
bash bin/neo4j_golden_dump.sh /home/idona/.neo4j_keeper_gate.env
```
The script detects whether systemd or pm2 manages Neo4j. **If it refuses
because it cannot prove the manager, you stop and report — you do not
guess, you do not stop processes by hand.**
Verify afterward: dump file exists, `.sha256` beside it, both `chmod 444`.

### Step 3 — Restore drill. A dump never loaded is a prayer.
```bash
bash bin/restore_drill.sh /home/idona/.neo4j_keeper_gate.env 90000
```
Must print `DRILL PASSED`. If Docker is absent, report — do not improvise
a drill against any running instance.

### Step 4 — Tripwire + nightly dump on cron
First confirm cron actually runs in this WSL instance:
```bash
systemctl is-system-running   # if this fails, report — cron may be dead in WSL
```
Then:
```cron
* * * * * /path/to/bin/neo4j_tripwire.sh /home/idona/.neo4j_keeper_gate.env >> /home/idona/neo4j_tripwire.log 2>&1
0 3 * * * /path/to/bin/neo4j_golden_dump.sh /home/idona/.neo4j_keeper_gate.env --daily >> /home/idona/neo4j_dumps/dump.log 2>&1
```
The truce flag (`/tmp/neo4j_maintenance`) is already coordinated between them.

### Step 5 — Firewall into every service
Every service that writes to Neo4j (CrypSide, Idim, Grid, MoEdge) replaces
direct `session.run(query)` calls with:
```python
from cypher_guard import run_cypher
run_cypher(session, query, **params)
```
No service keeps a raw `session.run` path for writes. Grep proof required:
```bash
grep -rn "session.run" --include="*.py" --include="*.ts" | grep -v cypher_guard
```
Submit that grep output as evidence of completion.

### Step 6 — Runtime split (your real work)
Migrate `Signal`, `ExecutionLog`, `ExecutorHeartbeat` out of the sacred graph
into the runtime store. When — and only when — migration is verified, write:
```
/home/idona/runtime_split_migrated.receipt
```
containing exactly:
```
Signal migrated
ExecutionLog migrated
ExecutorHeartbeat migrated
```
Plus the verification evidence (counts before/after) below those lines.
**Writing this receipt without completed migration is falsification of provenance.**

### Step 7 — Read-only (refuses without the receipt — by design)
```bash
sudo python3 bin/apply_neo4j_readonly.py /home/idona/.neo4j_keeper_gate.env /etc/neo4j/neo4j.conf
```

---

## ABSOLUTE PROHIBITIONS

1. **No destructive Cypher** (`DETACH DELETE`, `DROP`, APOC bulk/tunnel calls)
   outside `keeper_gate.execute()`. The gate refuses the production port
   under all circumstances — there is no override and you will not build one.
2. **No test fixtures, demo seeds, or wipe scripts** pointed at the prod port.
   Tests get a disposable instance on its own port. Always.
3. **No editing** `cypher_guard.py`, `keeper_gate.py`, or this file.
   Gaps or false positives → report to Flame; the audit (Claude) patches the guard.
4. **No comment is a safety mechanism.** `# clear test graph` is not a check.
   If your code's safety depends on a comment being true, the code is wrong.
5. **The golden dump directory is append-only territory.** Never delete,
   never overwrite outside the dump script itself.

## ACCEPTANCE — what "done" means
- [ ] `tests/selftest.py` → ALL PASS on Node Zero
- [ ] Golden dump + checksum exist, read-only, drill PASSED
- [ ] Both cron entries live and logging
- [ ] grep evidence: zero raw write paths bypassing `run_cypher`
- [ ] Tripwire manually tested once against a throwaway instance (NOT prod)
- [ ] Ledger at `keeper_gate_ledger.jsonl` shows your test events

Report each checkbox with evidence. Claims without evidence are not progress.

*"A comment is not a covenant. A name is not a port."* 🜃
