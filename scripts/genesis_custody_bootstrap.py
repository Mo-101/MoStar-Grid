#!/usr/bin/env python3
"""Digest-bound, fail-closed Genesis custody bootstrap for production Neo4j."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import unicodedata
import uuid
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

from dotenv import load_dotenv
from neo4j import GraphDatabase, READ_ACCESS, WRITE_ACCESS

ROOT = Path(__file__).resolve().parents[1]
CONSTITUTION = ROOT / "core/ops/governance/GRID_MIND_CONSTITUTION.md"
EVIDENCE = ROOT / "core/ops/status/GENESIS_CUSTODY_EVIDENCE.json"
CANONICALIZATION_ALGORITHM = "UTF8_BOM_STRIP+NEWLINE_LF+UNICODE_NFC+SINGLE_TRAILING_LF"
CANONICALIZATION_VERSION = "1"
ACTION = "GENESIS_CONSTITUTION_BOOTSTRAP"


def canonical_bytes() -> bytes:
    text = CONSTITUTION.read_text(encoding="utf-8-sig")
    text = unicodedata.normalize("NFC", text.replace("\r\n", "\n").replace("\r", "\n"))
    return (text.rstrip("\n") + "\n").encode("utf-8")


def constitution_hash() -> str:
    return hashlib.sha256(canonical_bytes()).hexdigest()


def now() -> datetime:
    return datetime.now(timezone.utc)


def git_identity() -> dict[str, str]:
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    dirty = subprocess.run(["git", "diff", "--quiet"], cwd=ROOT).returncode != 0
    untracked = subprocess.check_output(["git", "ls-files", "--others", "--exclude-standard"], cwd=ROOT, text=True).strip()
    return {"commit": commit, "worktree_state": "WORKTREE_UNCOMMITTED" if dirty or untracked else "CLEAN"}


def connection():
    load_dotenv(ROOT / ".env")
    load_dotenv(ROOT / "back/services/grid/.env", override=False)
    uri = os.environ["NEO4J_URI"]
    database = os.getenv("NEO4J_DATABASE", "neo4j")
    driver = GraphDatabase.driver(uri, auth=(os.getenv("NEO4J_USER", "neo4j"), os.environ["NEO4J_PASSWORD"]))
    return driver, uri, database


def preflight(session, digest: str) -> dict:
    components = session.run(
        "CALL dbms.components() YIELD name, versions, edition RETURN name, versions, edition"
    ).data()
    constraints = session.run(
        "SHOW CONSTRAINTS YIELD name, type, entityType, labelsOrTypes, properties "
        "RETURN name, type, entityType, labelsOrTypes, properties"
    ).data()
    required = [
        row for row in constraints
        if row["entityType"] == "NODE"
        and "Constitution" in row["labelsOrTypes"]
        and row["properties"] == ["constitution_hash"]
        and row["type"] in {"UNIQUENESS", "NODE_KEY"}
    ]
    counts = session.run(
        "MATCH (n) WHERE n:Constitution OR n:Provenance OR n:Attestation "
        "RETURN count(CASE WHEN n:Constitution THEN 1 END) AS constitution_count, "
        "count(CASE WHEN n:Provenance THEN 1 END) AS provenance_count, "
        "count(CASE WHEN n:Attestation THEN 1 END) AS attestation_count"
    ).single().data()
    target = session.run(
        "MATCH (c:Constitution {constitution_hash:$h}) "
        "OPTIONAL MATCH (c)-[:ORIGINATES_FROM]->(p:Provenance)-[:ATTESTED_BY]->(a:Attestation) "
        "RETURN count(DISTINCT c) AS roots, count(*) AS chains, "
        "sum(CASE WHEN p.constitution_hash=$h AND a.constitution_hash=$h AND a.subject_digest=$h THEN 1 ELSE 0 END) AS valid",
        h=digest,
    ).single().data()
    state = "EMPTY" if all(value == 0 for value in counts.values()) else "EXISTING"
    if state != "EMPTY":
        outcome = "ABORT_GENESIS_ALREADY_INITIALIZED" if target["valid"] == 1 else "ABORT_GENESIS_STATE_CONFLICT"
    elif not required:
        outcome = "ABORT_GENESIS_CONSTRAINT_MISSING"
    else:
        outcome = "READY_FOR_DIGEST_BOUND_HUMAN_AUTHORIZATION"
    return {
        "outcome": outcome,
        "dbms": components,
        "constraints": constraints,
        "required_constitution_constraint": required,
        "governance_counts": counts,
        "target_digest_state": target,
    }


def validate_authorization(path: Path, digest: str, environment: str) -> dict:
    auth = json.loads(path.read_text(encoding="utf-8"))
    required = {"action", "constitution_hash", "environment", "authorization_id", "issued_at", "valid_until", "nonce", "actor_ref"}
    missing = sorted(required - auth.keys())
    if missing:
        raise RuntimeError("ABORT_HUMAN_AUTHORIZATION_INCOMPLETE:" + ",".join(missing))
    if auth["action"] != ACTION or auth["constitution_hash"] != digest or auth["environment"] != environment:
        raise RuntimeError("ABORT_AUTHORIZED_DIGEST_MISMATCH")
    instant = now()
    issued = datetime.fromisoformat(auth["issued_at"].replace("Z", "+00:00"))
    expires = datetime.fromisoformat(auth["valid_until"].replace("Z", "+00:00"))
    if not issued <= instant <= expires:
        raise RuntimeError("ABORT_HUMAN_AUTHORIZATION_EXPIRED_OR_NOT_YET_VALID")
    return auth


def execute_tx(tx, digest: str, event_id: str, auth: dict) -> dict:
    # Preflight established a genuinely empty Genesis state. CREATE makes any
    # unexpected uniqueness race fail instead of silently matching ambiguity.
    row = tx.run(
        "CREATE (c:Constitution {constitution_hash:$h, lineage:'GENESIS', previous_hash:null, genesis_event_id:$event}) "
        "CREATE (p:Provenance {provenance_id:$pid, constitution_hash:$h, genesis_event_id:$event}) "
        "CREATE (a:Attestation {attestation_id:$aid, constitution_hash:$h, subject_digest:$h, genesis_event_id:$event, authorization_id:$authorization_id, actor_ref:$actor_ref}) "
        "CREATE (c)-[:ORIGINATES_FROM]->(p) "
        "CREATE (p)-[:ATTESTED_BY]->(a) "
        "RETURN elementId(c) AS constitution_id, elementId(p) AS provenance_id, elementId(a) AS attestation_id",
        h=digest,
        event=event_id,
        pid=f"genesis-provenance:{digest}",
        aid=f"genesis-attestation:{digest}",
        authorization_id=auth["authorization_id"],
        actor_ref=auth["actor_ref"],
    ).single().data()
    proof = tx.run(
        "MATCH (c:Constitution {constitution_hash:$h})-[:ORIGINATES_FROM]->(p:Provenance)-[:ATTESTED_BY]->(a:Attestation) "
        "RETURN c.constitution_hash AS constitution_hash, p.constitution_hash AS provenance_hash, "
        "a.constitution_hash AS attestation_hash, a.subject_digest AS attestation_subject_digest",
        h=digest,
    ).data()
    if len(proof) != 1 or set(proof[0].values()) != {digest}:
        raise RuntimeError("ABORT_POST_WRITE_UNIQUE_COMPOSITION_FAILED")
    return {"safe_graph_identifiers": row, "result_rows": proof}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("preflight", "execute"))
    parser.add_argument("--authorization", type=Path)
    args = parser.parse_args()
    digest = constitution_hash()
    driver, uri, database = connection()
    environment = f"{urlparse(uri).scheme}://{urlparse(uri).hostname}/{database}"
    base = {
        "schema": "mostar.genesis-custody-evidence.v1",
        "recorded_at": now().isoformat(),
        "action": ACTION,
        "environment": environment,
        "canonicalization_algorithm": CANONICALIZATION_ALGORITHM,
        "canonicalization_version": CANONICALIZATION_VERSION,
        "digest_algorithm": "SHA-256",
        "constitution_hash": digest,
        "lineage": "GENESIS",
        "previous_hash": None,
        **git_identity(),
    }
    with driver:
        driver.verify_connectivity()
        with driver.session(database=database, default_access_mode=READ_ACCESS) as session:
            check = preflight(session, digest)
        base["preflight"] = check
        if args.mode == "preflight":
            base["bootstrap_executed"] = False
            base["human_authorization"] = "ABSENT"
            EVIDENCE.write_text(json.dumps(base, indent=2) + "\n", encoding="utf-8")
            print(json.dumps(base, indent=2))
            return 0 if check["outcome"].startswith("READY_") else 1
        if check["outcome"] != "READY_FOR_DIGEST_BOUND_HUMAN_AUTHORIZATION":
            raise RuntimeError(check["outcome"])
        if not args.authorization:
            raise RuntimeError("ABORT_HUMAN_AUTHORIZATION_REQUIRED")
        auth = validate_authorization(args.authorization, digest, environment)
        event_id = str(uuid.uuid4())
        with driver.session(database=database, default_access_mode=WRITE_ACCESS) as session:
            result = session.execute_write(execute_tx, digest, event_id, auth)
        base.update({
            "bootstrap_executed": True,
            "bootstrap_event_id": event_id,
            "human_authorization": "PRESENT",
            "authorization": {key: auth[key] for key in ("authorization_id", "issued_at", "valid_until", "nonce", "actor_ref")},
            "dispositions": {"constitution": "CREATED", "provenance": "CREATED", "attestation": "CREATED", "relationships": "CREATED"},
            "execution": result,
            "result": "UNIQUE_GENESIS_CHAIN_VERIFIED",
        })
        EVIDENCE.write_text(json.dumps(base, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(base, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
