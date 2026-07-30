import json
from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from grid.config import MOSTAR_CLUSTER_ID, NEO4J_DATABASE


router = APIRouter(tags=["mostar-gap-register"])


GAP_REGISTER = [
    {
        "id": "GAP-001",
        "domain": "truth-governance",
        "title": "Threshold inconsistency across Soul/Mind",
        "risk": "approval behavior can diverge across components",
        "epic": "Epic 1: Canonical truth and policy",
        "priority": 2,
        "tasks": [
            "canonical threshold registry",
            "layer-specific override precedence",
            "decision record for every threshold evaluation",
            "Soul/Mind/Body parity fixtures",
        ],
        "acceptance": "Identical inputs produce the same effective threshold outcome unless an explicit override exists.",
    },
    {
        "id": "GAP-002",
        "domain": "truth-governance",
        "title": "Policy and ownership boundaries are underdefined",
        "risk": "symbolic truth, runtime truth, and persistence can drift",
        "epic": "Epic 1: Canonical truth and policy",
        "priority": 2,
        "tasks": [
            "ownership matrix for canonical node families",
            "source-of-truth table",
            "mutation policy by artifact family",
        ],
        "acceptance": "Every canonical entity has one authoritative write path and one provenance policy.",
    },
    {
        "id": "GAP-003",
        "domain": "truth-governance",
        "title": "Sealed vs mutable artifact semantics are not explicit enough",
        "risk": "sealed graph truth can be overwritten instead of superseded",
        "epic": "Epic 1: Canonical truth and policy",
        "priority": 2,
        "tasks": [
            "immutable-state contract for sealed moments",
            "supersession model",
            "audit reason codes",
            "quarantine path for invalid artifacts",
        ],
        "acceptance": "No sealed artifact is modified directly; it is superseded with lineage preserved.",
    },
    {
        "id": "GAP-004",
        "domain": "runtime-failure",
        "title": "Rollback and replay semantics are missing",
        "risk": "orchestration writes can become brittle or non-repeatable",
        "epic": "Epic 2: Safe runtime",
        "priority": 4,
        "tasks": ["rollback specs", "idempotency keys", "replay-safe handlers", "dead-letter queue"],
        "acceptance": "Every mutation flow documents forward action, compensating action, and replay behavior.",
    },
    {
        "id": "GAP-005",
        "domain": "runtime-failure",
        "title": "Queueing and recomputation boundaries are unclear",
        "risk": "secondary projections can cause latency spikes or partial writes",
        "epic": "Epic 2: Safe runtime",
        "priority": 4,
        "tasks": ["sync/async split table", "recomputation queue", "retry with jitter", "stale-read markers"],
        "acceptance": "Primary writes commit fast; secondary projections are durable and observable.",
    },
    {
        "id": "GAP-006",
        "domain": "runtime-failure",
        "title": "Offline-first behavior is not yet operationalized",
        "risk": "critical workflows degrade silently under network loss",
        "epic": "Epic 2: Safe runtime",
        "priority": 7,
        "tasks": ["local persistence", "write-ahead queue", "sync conflict policy", "stale-data annotations"],
        "acceptance": "Core reads/writes and recommendations continue under network loss with explicit fidelity signals.",
    },
    {
        "id": "GAP-007",
        "domain": "graph-neo4j",
        "title": "Traversal safety and query budgets are not formalized",
        "risk": "public APIs can trigger expensive or unsafe graph scans",
        "epic": "Epic 3: Graph/API hardening",
        "priority": 3,
        "tasks": ["approved Cypher catalog", "max-depth policies", "timeout and row-limit defaults", "procedure allowlist"],
        "acceptance": "No API path can trigger an unbounded traversal or unrestricted procedure.",
    },
    {
        "id": "GAP-008",
        "domain": "graph-neo4j",
        "title": "Canonical relationship normalization is still needed",
        "risk": "overlapping edge vocabulary reduces graph interpretability",
        "epic": "Epic 1: Canonical truth and policy",
        "priority": 3,
        "tasks": ["relationship taxonomy", "allowed-from/to schema", "deprecation list", "validation job"],
        "acceptance": "Every relation type has clear semantics, direction, and allowed label pairs.",
    },
    {
        "id": "GAP-009",
        "domain": "graph-neo4j",
        "title": "Runtime telemetry assembly needs governance",
        "risk": "dashboards can rely on arbitrary raw graph reads",
        "epic": "Epic 3: Graph/API hardening",
        "priority": 5,
        "tasks": ["canonical telemetry views", "event classification", "redaction policy", "audit access policy"],
        "acceptance": "Dashboards and APIs read from curated projections, not arbitrary raw graph scans.",
    },
    {
        "id": "GAP-010",
        "domain": "api-interactivity",
        "title": "API contract is not yet aligned to artifact provenance",
        "risk": "responses cannot be traced to source artifacts and policy decisions",
        "epic": "Epic 3: Graph/API hardening",
        "priority": 5,
        "tasks": ["standard response envelope", "error taxonomy", "mutation receipts", "policy evaluation in privileged responses"],
        "acceptance": "Every API response can be traced to source artifacts and policy decisions.",
    },
    {
        "id": "GAP-011",
        "domain": "api-interactivity",
        "title": "Interactivity rules across grid entities are not explicit",
        "risk": "artifact updates have undocumented downstream effects",
        "epic": "Epic 4: Decision and interaction fabric",
        "priority": 6,
        "tasks": ["impact map", "neighbor propagation rules", "reindex triggers", "UI subscription model"],
        "acceptance": "Updating a moment/persona/lifestage has a documented downstream effect map.",
    },
    {
        "id": "GAP-012",
        "domain": "decision-explanation",
        "title": "DeepCAL integration needs boundary definition",
        "risk": "decision runs cannot be reconstructed from stored evidence",
        "epic": "Epic 4: Decision and interaction fabric",
        "priority": 7,
        "tasks": ["DeepCAL adapter boundary", "graph-to-criteria mapping", "recommendation storage", "offline fallback"],
        "acceptance": "A decision run can be reconstructed from stored inputs, weights, outcomes, and evidence.",
    },
    {
        "id": "GAP-013",
        "domain": "decision-explanation",
        "title": "Personality/persona behavior needs constraint boundaries",
        "risk": "persona tone can distort factual truth or permissions",
        "epic": "Epic 4: Decision and interaction fabric",
        "priority": 7,
        "tasks": ["persona rendering policy", "forbidden transformations", "evidence-preserving templates", "tone versioning"],
        "acceptance": "Personality affects phrasing, not underlying truth, evidence, or permissions.",
    },
    {
        "id": "GAP-014",
        "domain": "security",
        "title": "Compromised secret handling is an active issue",
        "risk": "exposed credentials may remain valid",
        "epic": "Epic 5: Security and lineage recovery",
        "priority": 1,
        "tasks": ["rotate/revoke exposed credentials", "remove secrets from repos/history", "move to secret manager", "quarantine files"],
        "acceptance": "No active credential from the compromised file remains valid anywhere.",
    },
    {
        "id": "GAP-015",
        "domain": "security",
        "title": "Authz model for graph mutation is not yet demonstrated",
        "risk": "write paths can bypass governance",
        "epic": "Epic 3: Graph/API hardening",
        "priority": 3,
        "tasks": ["subject/action/resource matrix", "least-privilege graph roles", "break-glass policy", "approval gates"],
        "acceptance": "Every write path has a documented authz check and audit trail.",
    },
    {
        "id": "GAP-016",
        "domain": "data-lineage",
        "title": "Dataset/version/correction lifecycle needs a closed loop",
        "risk": "corrections are not first-class or reversible",
        "epic": "Epic 5: Security and lineage recovery",
        "priority": 7,
        "tasks": ["ingestion-to-curation workflow", "reconciliation queues", "correction workflow", "confidence/status fields"],
        "acceptance": "Data corrections are first-class, reversible, and linked to downstream impact.",
    },
    {
        "id": "GAP-017",
        "domain": "data-lineage",
        "title": "Versioning policy across persona, lifestage, API, and moments is incomplete",
        "risk": "clients cannot safely interpret migration status",
        "epic": "Epic 5: Security and lineage recovery",
        "priority": 7,
        "tasks": ["global versioning policy", "compatibility matrix", "supersession edges", "migration playbooks"],
        "acceptance": "Clients can safely interpret artifact versions and migration status.",
    },
    {
        "id": "GAP-018",
        "domain": "delivery-operations",
        "title": "No explicit rollout and rollback governance for major changes",
        "risk": "major changes can ship without owner, metrics, or rollback trigger",
        "epic": "Epic 2: Safe runtime",
        "priority": 8,
        "tasks": ["release template", "canary plan", "readiness checklist", "post-deploy audit capture"],
        "acceptance": "No major change ships without owner, metrics, rollback trigger, and audit evidence.",
    },
]


class GapStatusUpdate(BaseModel):
    status: str = Field(..., min_length=1, max_length=80)
    owner: Optional[str] = Field(default=None, max_length=160)
    note: Optional[str] = Field(default=None, max_length=1000)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _require_driver(request: Request):
    orchestrator = request.app.state.orchestrator
    if not orchestrator.mindgraph.connected or orchestrator.mindgraph._driver is None:
        raise HTTPException(503, "MindGraph not connected")
    return orchestrator.mindgraph._driver


def _by_id(gap_id: str) -> dict[str, Any]:
    for gap in GAP_REGISTER:
        if gap["id"] == gap_id:
            return gap
    raise HTTPException(404, f"Gap {gap_id} not found")


@router.get("/mostar/gaps")
async def list_gaps(domain: Optional[str] = None, epic: Optional[str] = None):
    gaps = GAP_REGISTER
    if domain:
        gaps = [gap for gap in gaps if gap["domain"] == domain]
    if epic:
        gaps = [gap for gap in gaps if gap["epic"] == epic]
    return {
        "total": len(gaps),
        "gaps": sorted(gaps, key=lambda item: (item["priority"], item["id"])),
    }


@router.get("/mostar/gaps/{gap_id}")
async def get_gap(gap_id: str):
    return _by_id(gap_id)


@router.get("/mostar/gaps/{gap_id}/remediation")
async def get_gap_remediation(gap_id: str):
    gap = _by_id(gap_id)
    return {
        "gap_id": gap["id"],
        "epic": gap["epic"],
        "priority": gap["priority"],
        "risk": gap["risk"],
        "tasks": gap["tasks"],
        "acceptance": gap["acceptance"],
    }


@router.post("/mostar/gaps/sync")
async def sync_gaps_to_graph(request: Request):
    driver = _require_driver(request)
    now = _now()
    async with driver.session(database=NEO4J_DATABASE) as session:
        result = await session.run(
            """
            UNWIND $gaps AS gap
            MERGE (g:GapRegisterItem {gap_id: gap.id})
            SET g.domain = gap.domain,
                g.title = gap.title,
                g.risk = gap.risk,
                g.priority = gap.priority,
                g.acceptance = gap.acceptance,
                g.cluster_id = $cluster_id,
                g.updated_at = $now,
                g.status = coalesce(g.status, 'open')
            MERGE (track:RemediationTrack {name: gap.epic})
            SET track.cluster_id = $cluster_id,
                track.updated_at = $now
            MERGE (g)-[:REMEDIATED_BY]->(track)
            WITH g, gap
            UNWIND gap.tasks AS task
            MERGE (t:RemediationTask {gap_id: gap.id, title: task})
            SET t.cluster_id = $cluster_id,
                t.updated_at = $now,
                t.status = coalesce(t.status, 'planned')
            MERGE (g)-[:HAS_REMEDIATION_TASK]->(t)
            RETURN count(DISTINCT g) AS gaps, count(DISTINCT t) AS tasks
            """,
            gaps=GAP_REGISTER,
            cluster_id=MOSTAR_CLUSTER_ID,
            now=now,
        )
        record = await result.single()
        await session.run(
            """
            MERGE (evt:RuntimeEvent {event_id: $event_id})
            SET evt.type = 'GAP_REGISTER_SYNCED',
                evt.created_at = $now,
                evt.cluster_id = $cluster_id,
                evt.payload = $payload
            """,
            event_id=f"gap_register_synced_{now}",
            now=now,
            cluster_id=MOSTAR_CLUSTER_ID,
            payload=json.dumps({"gaps": len(GAP_REGISTER)}, sort_keys=True),
        )
    return {
        "synced": True,
        "gaps": record["gaps"] if record else 0,
        "tasks": record["tasks"] if record else 0,
        "runtime_event": "GAP_REGISTER_SYNCED",
    }


@router.patch("/mostar/gaps/{gap_id}/status")
async def update_gap_status(gap_id: str, payload: GapStatusUpdate, request: Request):
    _by_id(gap_id)
    driver = _require_driver(request)
    now = _now()
    async with driver.session(database=NEO4J_DATABASE) as session:
        result = await session.run(
            """
            MATCH (g:GapRegisterItem {gap_id: $gap_id})
            SET g.status = $status,
                g.owner = $owner,
                g.last_note = $note,
                g.updated_at = $now
            CREATE (evt:RuntimeEvent {
                event_id: $event_id,
                type: 'GAP_STATUS_UPDATED',
                gap_id: $gap_id,
                status: $status,
                note: $note,
                created_at: $now,
                cluster_id: $cluster_id
            })
            MERGE (g)-[:EMITTED_EVENT]->(evt)
            RETURN g, evt
            """,
            gap_id=gap_id,
            status=payload.status,
            owner=payload.owner,
            note=payload.note,
            now=now,
            event_id=f"gap_status_{gap_id}_{now}",
            cluster_id=MOSTAR_CLUSTER_ID,
        )
        record = await result.single()
    if not record:
        raise HTTPException(404, f"Gap {gap_id} has not been synced to graph")
    return {"gap": dict(record["g"]), "runtime_event": dict(record["evt"])}
