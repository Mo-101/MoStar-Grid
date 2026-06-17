#!/usr/bin/env python3
"""Cold proof. Run: python3 tests/selftest.py — must print ALL PASS before deployment."""

import os
import sys
import time
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "guard"))

from cypher_guard import assert_safe_cypher, BlockedCypher
from keeper_gate import KeeperGate, CovenantBreach

results = []


def check(name, fn, expect_raise=None):
    try:
        fn()
        ok = expect_raise is None
    except Exception as e:
        ok = expect_raise is not None and isinstance(e, expect_raise)
    results.append((ok, name))
    print(f"{'✓' if ok else '✗ FAIL'} {name}")


# ── Firewall ──────────────────────────────────────────────────────────────
check("read passes", lambda: assert_safe_cypher("MATCH (n:Odu) RETURN n LIMIT 5"))
check("MERGE with props passes", lambda: assert_safe_cypher("MERGE (m:MoStarMoment {id:'mm-x'}) SET m.sealed=true"))
check("scoped delete passes", lambda: assert_safe_cypher("MATCH (n:Fixture) WHERE n.id = $id DELETE n"))
check("DETACH DELETE blocked", lambda: assert_safe_cypher("MATCH (n) DETACH DELETE n"), BlockedCypher)
check("DROP DATABASE blocked", lambda: assert_safe_cypher("DROP DATABASE neo4j"), BlockedCypher)
check("apoc.periodic.iterate blocked",
      lambda: assert_safe_cypher("CALL apoc.periodic.iterate('MATCH (n) RETURN n','DELETE n',{})"), BlockedCypher)
check("apoc.cypher.run blocked", lambda: assert_safe_cypher("CALL apoc.cypher.run('MATCH (n) DELETE n', {})"), BlockedCypher)
check("apoc.do.when blocked", lambda: assert_safe_cypher("CALL apoc.do.when(true,'DELETE n','',{})"), BlockedCypher)
check("apoc.nodes.delete blocked", lambda: assert_safe_cypher("CALL apoc.nodes.delete(nodes, 1000)"), BlockedCypher)
check("bare DELETE without WHERE blocked", lambda: assert_safe_cypher("MATCH (n) DELETE n"), BlockedCypher)

# ── Keeper Gate ───────────────────────────────────────────────────────────
tmp = tempfile.mkdtemp()
backup_dir = Path(tmp) / "golden"
backup_dir.mkdir()
gate = KeeperGate(prod_port=47687, backup_dir=str(backup_dir),
                  ledger_path=str(Path(tmp) / "ledger.jsonl"))
os.environ["FLAME_SEAL"] = "test-seal-phrase"

# Prod port: never lawful, even with perfect keys
fresh = backup_dir / "neo4j.dump"
fresh.write_bytes(b"x" * 1024)
check("PROD port refused absolutely",
      lambda: gate.seal("bolt://127.0.0.1:47687", 95115, "test-seal-phrase"), CovenantBreach)

# Wrong token refused
check("bad token refused",
      lambda: gate.seal("bolt://127.0.0.1:41687", 42, "wrong"), CovenantBreach)

# Stale backup refused
old_time = time.time() - 7200
os.utime(fresh, (old_time, old_time))
check("stale backup refused",
      lambda: gate.seal("bolt://127.0.0.1:41687", 42, "test-seal-phrase"), CovenantBreach)

# All three keys → seal granted (non-prod only)
fresh.touch()
check("three keys grant seal (non-prod)",
      lambda: gate.seal("bolt://127.0.0.1:41687", 42, "test-seal-phrase"))

# URI without port refused
check("portless URI refused",
      lambda: gate.seal("bolt://localhost", 42, "test-seal-phrase"), CovenantBreach)

# ── Verdict ───────────────────────────────────────────────────────────────
failed = [n for ok, n in results if not ok]
print()
if failed:
    print(f"FAILED: {failed}")
    sys.exit(1)
print(f"ALL PASS ({len(results)}/{len(results)}). The wall stands. The gate counts. 🜃")
