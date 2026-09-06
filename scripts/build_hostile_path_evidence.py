#!/usr/bin/env python3
"""Convert a real Vitest JSON run into canonical post-closure HP evidence."""
from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CASES = {
    "HP-1": "HP-1 rejects freeform Cypher before driver execution",
    "HP-2": "HP-2 rejects Cypher-shaped text as query_key",
    "HP-3": "HP-3 blocks model self-attestation",
    "HP-4A": "HP-4 actual failure ETIMEDOUT refuses snapshot and inference",
    "HP-4B": "HP-4 actual failure 503 Service Unavailable refuses snapshot and inference",
    "HP-5": "HP-5 excludes withdrawn, restricted, consent-denied, and derivation-denied claims",
    "HP-6": "HP-6 stacked attack halts at binding before every downstream capability",
    "HP-7": "HP-7A rejects direct DCX invocation through the universal adapter",
    "HP-8": "HP-8 blocks an online, correctly signed model after constitutional drift",
    "HP-9": "HP-9 withholds a receipt when all six gates pass but HumanAuthorization is absent",
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("vitest_json", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    raw = json.loads(args.vitest_json.read_text(encoding="utf-8"))
    assertions = []
    for result in raw.get("testResults", []):
        path = str(Path(result.get("name", "")).resolve().relative_to(ROOT))
        for assertion in result.get("assertionResults", []):
            assertions.append((assertion.get("fullName", ""), assertion.get("status"), path, assertion.get("failureMessages", [])))
    executed_at = datetime.now(timezone.utc).isoformat()
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    cases = []
    for hp_id, symbol in CASES.items():
        match = next((item for item in assertions if symbol in item[0]), None)
        cases.append({
            "id": hp_id,
            "test_path": match[2] if match else None,
            "test_symbol": symbol,
            "executed_at": executed_at,
            "commit": commit,
            "worktree_state": "WORKTREE_UNCOMMITTED",
            "result": "PASS" if match and match[1] == "passed" else "FAIL",
            "failure_reason": None if match and match[1] == "passed" else (match[3] if match else ["TEST_NOT_FOUND"]),
        })
    document = {
        "schema": "mostar.hostile-path-evidence.v1",
        "suite": "POST_INVOCATION_CLOSURE",
        "executed_at": executed_at,
        "commit": commit,
        "worktree_state": "WORKTREE_UNCOMMITTED",
        "all_cases_passed": all(case["result"] == "PASS" for case in cases),
        # The disposition used to be the literal "UNVERIFIED" with the reason
        # "ISOLATED_HP_CASES_PASS; SYSTEM_COMPOSITION_GUARDS_REMAIN_UNVERIFIED",
        # written whether the cases passed or failed. That was true while the
        # live constitution composition could not be proven against the graph;
        # it is now proven separately (LIVE_CONSTITUTION_COMPOSITION_EVIDENCE),
        # and the census reads that gate on its own. This file now reports only
        # what this run measured, and the census refuses evidence whose commit
        # is not the tree under audit.
        "gate_disposition": "PASS" if all(case["result"] == "PASS" for case in cases) else "FAILED",
        "gate_reason": "ALL_POST_CLOSURE_HP_CASES_PASS_AT_THIS_COMMIT"
        if all(case["result"] == "PASS" for case in cases)
        else "HP_CASES_FAILED:" + ",".join(c["id"] for c in cases if c["result"] != "PASS"),
        "cases": cases,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")
    return 0 if document["all_cases_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
