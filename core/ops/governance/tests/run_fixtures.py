#!/usr/bin/env python3
"""Constitutional fixture runner. FAILS CLOSED.

Runs every negative fixture against an EPHEMERAL test database inside a
transaction that is always rolled back. Production Neo4j is never touched.

Gates are loaded from the committed .cypher files — not from copies pasted
in here. Testing a copy would verify the copy, not the gate that ships.

Fail-closed rules (a run that verifies nothing must never report success):
    zero fixtures discovered                      -> ERROR
    zero gates loaded                             -> ERROR
    expected-violation fixture returns zero rows  -> ERROR
    gate fails but not for the expected id        -> ERROR
    unexpected violation in a gate expected clean -> ERROR

Usage:
    NEO4J_TEST_URI=bolt://127.0.0.1:47688 python3 run_fixtures.py
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

from neo4j import GraphDatabase

HERE = Path(__file__).resolve().parent
GOV = HERE.parent / "neo4j"
GATES_DIR = GOV / "gates"
AUDIT_GATE = HERE.parent.parent / "audit" / "neo4j" / "governance_vocabulary_drift.cypher"
BASELINE = GOV / "migrations" / "000_current_governance_baseline.cypher"

sys.path.insert(0, str(HERE))
from fixtures import VALID, FIXTURES  # noqa: E402

URI = os.environ.get("NEO4J_TEST_URI", "bolt://127.0.0.1:47688")
DB = os.environ.get("NEO4J_TEST_DATABASE", "neo4j")

# gate name -> file. Reconstruction takes a param and is exercised separately.
GATE_FILES = {
    "promotion_presence": GATES_DIR / "promotion_presence.cypher",
    "promotion_shape": GATES_DIR / "promotion_shape.cypher",
    "authorization_cardinality": GATES_DIR / "authorization_cardinality.cypher",
    "executor_cardinality": GATES_DIR / "executor_cardinality.cypher",
    "decision_topology": GATES_DIR / "decision_topology.cypher",
    "quorum_recomputation": GATES_DIR / "quorum_recomputation.cypher",
    "vocabulary_drift": AUDIT_GATE,
}


def load_gate(path: Path) -> str:
    body = "\n".join(
        line for line in path.read_text(encoding="utf-8").splitlines()
        if not line.strip().startswith("//")
    ).strip()
    return body.rstrip(";").strip()


def load_baseline() -> list[str]:
    text = BASELINE.read_text(encoding="utf-8")
    text = "\n".join(l for l in text.splitlines() if not l.strip().startswith("//"))
    return [s.strip() for s in text.split(";") if s.strip()]


def row_ids(rows) -> set[str]:
    out: set[str] = set()
    for r in rows:
        for v in r.values():
            if isinstance(v, str):
                out.add(v)
            elif isinstance(v, list):
                out.update(x for x in v if isinstance(x, str))
    return out


def main() -> int:
    gates = {}
    for name, path in GATE_FILES.items():
        if not path.is_file():
            print(f"ERROR: gate file missing: {path}", file=sys.stderr)
            return 2
        gates[name] = load_gate(path)
    if not gates:
        print("ERROR: zero gates loaded", file=sys.stderr)
        return 2
    if not FIXTURES:
        print("ERROR: zero fixtures discovered", file=sys.stderr)
        return 2

    driver = GraphDatabase.driver(URI, auth=None)
    failures: list[str] = []
    results: dict[str, dict[str, bool]] = {}

    with driver.session(database=DB) as s:
        print(f"applying baseline to TEST db {URI} ...")
        for stmt in load_baseline():
            s.run(stmt)
        print(f"  {len(load_baseline())} schema statements applied\n")

        print(f"{'FIXTURE':<34}{'GATE':<28}{'ROWS':>5}  VERDICT")
        print("-" * 88)

        for fname, extra, expect in FIXTURES:
            tx = s.begin_transaction()
            try:
                tx.run(VALID)
                if extra.strip():
                    tx.run(extra)

                # COUNT{} subqueries always yield exactly one row. Chained
                # MATCHes returned NO row when a fixture deleted the
                # promotion, so the denominator vanished for precisely the
                # fixtures that most needed reporting.
                counts = tx.run(
                    "RETURN COUNT { (c:Claim) } AS claims, "
                    "COUNT { (p:CanonicalPromotion) } AS promos, "
                    "COUNT { (v:AdjudicationVote) } AS votes, "
                    "COUNT { (d:AdjudicationDecision) } AS decisions").single()

                results[fname] = {}
                for gname, expected_id in expect.items():
                    rows = list(tx.run(gates[gname]))
                    ids = row_ids(rows)
                    ok = True
                    note = ""

                    if expected_id is None:
                        if rows:
                            ok = False
                            note = f"unexpected violation: {sorted(ids)[:3]}"
                    else:
                        if not rows:
                            ok = False
                            note = f"EXPECTED violation {expected_id!r}, got zero rows"
                        elif expected_id not in ids:
                            ok = False
                            note = f"failed for wrong reason; want {expected_id!r} got {sorted(ids)[:3]}"

                    results[fname][gname] = ok
                    verdict = "ok" if ok else f"*** {note} ***"
                    exp = "clean" if expected_id is None else f"expect {expected_id}"
                    print(f"{fname:<34}{gname:<28}{len(rows):>5}  {verdict}  [{exp}]")
                    if not ok:
                        failures.append(f"{fname}/{gname}: {note}")

                den = (f"claims={counts['claims']} promotions={counts['promos']} "
                       f"decisions={counts['decisions']} votes={counts['votes']}"
                       if counts is not None else "*** denominator unavailable ***")
                print(f"{'':<34}{'(denominator)':<28}{'':>5}  {den}")
            finally:
                tx.rollback()
            print("-" * 88)

        left = s.run("MATCH (n) WHERE n.canonical_id STARTS WITH 'fx:' "
                     "RETURN count(n) AS c").single()["c"]
        print(f"\nfixture residue after rollback: {left} nodes "
              f"{'OK' if left == 0 else '*** LEAKED ***'}")
        if left:
            failures.append(f"fixture residue: {left} nodes survived rollback")

    driver.close()

    total = sum(len(v) for v in results.values())
    passed = sum(1 for v in results.values() for ok in v.values() if ok)
    print(f"\n{'=' * 88}\nfixtures={len(results)}  gate-assertions={total}  "
          f"passed={passed}  failed={len(failures)}")
    for f in failures:
        print(f"  FAIL {f}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
