"""Read-only projection of the single Mind Conduit evidence artifact."""
from __future__ import annotations

import json
from pathlib import Path

EVIDENCE_PATH = Path(__file__).resolve().parents[3] / "core/ops/status/MIND_CONDUIT_CANONICAL_EVIDENCE.json"
LIVE_GATES = (
    "MODEL_BINDING",
    "CYPHER_GUARD",
    "PROVENANCE_FILTER",
    "ATTESTATION_GUARD",
    "INVOCATION_SURFACE_GUARD",
    "HOSTILE_PATH_TEST",
)


def load_mind_conduit_status() -> dict:
    document = json.loads(EVIDENCE_PATH.read_text(encoding="utf-8"))
    if document.get("schema") != "mostar.mind-conduit-evidence.v1":
        raise RuntimeError("INVALID_MIND_CONDUIT_EVIDENCE_SCHEMA")
    gates = document.get("gates", {})
    if set(gates) != set(LIVE_GATES) or "INVOCATION_AUDIT" in gates:
        raise RuntimeError("INVALID_MIND_CONDUIT_GATE_SET")
    readiness = document.get("readiness", {})
    return {
        **gates,
        "MIND_CONDUIT": readiness["MIND_CONDUIT"],
        "GRID_MIND_READY": readiness["GRID_MIND_READY"],
        "blockers": readiness.get("blockers", []),
        "evidence_schema": document["schema"],
        "evidence_generated_at": document["generated_at"],
        "invocation_surface": document["invocation_surface"],
        "constitution_hash_lineage": document["constitution_hash_lineage"],
        "seal_receipt": document["seal_receipt"],
        "required_tags": ["MoScripts"],
        "invocation_scope": "ALL_PRESENT_AND_FUTURE_MODELS",
        "self_ratification_permitted": False,
    }
