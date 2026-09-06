#!/usr/bin/env python3
"""Read-only production Neo4j proof for the Genesis constitution chain."""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from neo4j import GraphDatabase

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "back" / "services")]
OUTPUT = ROOT / "core/ops/status/LIVE_CONSTITUTION_COMPOSITION_EVIDENCE.json"
SOURCE = ROOT / "front/app/src/lib/mind/constitution-composition.ts"
CONSTITUTION = ROOT / "core/ops/governance/GRID_MIND_CONSTITUTION.md"


def main() -> int:
    # Resolve Neo4j exactly as the running Grid does — grid.config loads
    # _apps/grid/.env and the password comes from the attested vault. This used
    # to read NEO4J_PASSWORD straight from the environment and fall back to a
    # second dotenv at back/services/grid/.env, a path that does not exist; with
    # the password living in the vault rather than any .env, the bare os.environ
    # lookup raised KeyError and this proof could not be run at all.
    from grid.config import (  # noqa: E402 — needs the sys.path prefix above
        NEO4J_DATABASE,
        NEO4J_URI,
        NEO4J_USER,
        get_neo4j_password,
    )

    source = SOURCE.read_text(encoding="utf-8")
    match = re.search(r"CONSTITUTION_CHAIN_CYPHER\s*=\s*`(?P<query>[\s\S]*?)`\.trim\(\)", source)
    if not match:
        raise RuntimeError("CANONICAL_COMPOSITION_QUERY_NOT_FOUND")
    query = match.group("query").strip()
    constitution_hash = hashlib.sha256(CONSTITUTION.read_bytes()).hexdigest()
    params = {"constitution_hash": constitution_hash}
    uri = NEO4J_URI
    user = NEO4J_USER
    password = get_neo4j_password()
    database = NEO4J_DATABASE
    driver_calls = 0
    with GraphDatabase.driver(uri, auth=(user, password)) as driver:
        driver.verify_connectivity()
        with driver.session(database=database, default_access_mode="READ") as session:
            rows = [record.data() for record in session.run(query, params)]
            driver_calls += 1
            root_count = session.run(
                "MATCH (c:Constitution {constitution_hash: $constitution_hash}) RETURN count(c) AS count",
                params,
            ).single()["count"]
            driver_calls += 1
            topology = session.run(
                """
                MATCH (c:Constitution {constitution_hash: $constitution_hash})
                MATCH (c)-[:ORIGINATES_FROM]->(p:Provenance)
                MATCH (p)-[:ATTESTED_BY]->(a:Attestation)
                RETURN count(*) AS chain_count,
                       sum(CASE WHEN p.constitution_hash = c.constitution_hash
                                     AND a.constitution_hash = c.constitution_hash
                                     AND a.subject_digest = c.constitution_hash
                                THEN 1 ELSE 0 END) AS fully_bound_count
                """,
                params,
            ).single()
            driver_calls += 1
    valid_chain_count = len(rows)
    competing_valid_chain_count = max(valid_chain_count - 1, 0)
    topology_count = int(topology["chain_count"] or 0)
    fully_bound_count = int(topology["fully_bound_count"] or 0)
    digest_conflict_count = topology_count - fully_bound_count
    result = (
        "PASS"
        if root_count == 1
        and valid_chain_count == 1
        and competing_valid_chain_count == 0
        and topology_count == 1
        and digest_conflict_count == 0
        and rows[0].get("attestation_subject_digest") == constitution_hash
        else "FAIL"
    )
    document = {
        "schema": "mostar.live-constitution-composition-evidence.v1",
        "executed_at": datetime.now(timezone.utc).isoformat(),
        "source_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "worktree_state": "WORKTREE_UNCOMMITTED",
        "read_only": True,
        "query_source": str(SOURCE.relative_to(ROOT)),
        "query_source_digest": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        "query": query,
        "bound_parameters": params,
        "database": database,
        "driver_calls": driver_calls,
        "result_rows": rows,
        "constitution_root_count": root_count,
        "valid_chain_count": valid_chain_count,
        "competing_valid_chain_count": competing_valid_chain_count,
        "topology_chain_count": topology_count,
        "digest_conflict_count": digest_conflict_count,
        "constitution_digest": constitution_hash,
        "previous_hash": None,
        "lineage": "GENESIS",
        "custody_record": "first authoritative record",
        "result": result,
        "failure_reasons": [
            reason
            for condition, reason in (
                (root_count != 1, f"CONSTITUTION_ROOT_COUNT:{root_count}"),
                (valid_chain_count != 1, f"VALID_CHAIN_COUNT:{valid_chain_count}"),
                (competing_valid_chain_count != 0, f"COMPETING_VALID_CHAIN_COUNT:{competing_valid_chain_count}"),
                (topology_count != 1, f"TOPOLOGY_CHAIN_COUNT:{topology_count}"),
                (digest_conflict_count != 0, f"DIGEST_CONFLICT_COUNT:{digest_conflict_count}"),
            )
            if condition
        ],
    }
    OUTPUT.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: document[key] for key in (
        "result", "constitution_root_count", "valid_chain_count",
        "competing_valid_chain_count", "topology_chain_count", "digest_conflict_count",
    )}))
    return 0 if result == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
