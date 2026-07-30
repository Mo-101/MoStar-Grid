import hashlib
import json
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from grid.config import MOSTAR_CLUSTER_ID, NEO4J_DATABASE, SEAL_GLYPH


router = APIRouter(tags=["mostar-artifacts"])


CANONICAL_NODE_TYPES = {
    "MoStarMoment": {
        "responsibility": "Atomic sealed stateful artifact of lived system intelligence.",
        "required": ["id", "quantum_id", "sealed_at", "mo_processed", "cluster_id"],
    },
    "LifeStage": {
        "responsibility": "Developmental context for permissions, posture, response shape, and workflow branching.",
        "required": ["key", "name"],
    },
    "Persona": {
        "responsibility": "Queryable behavioral context, connected to traits and resonance.",
        "required": ["id", "active"],
    },
    "PersonaTrait": {"responsibility": "Atomic persona trait.", "required": ["key"]},
    "ResonanceProfile": {"responsibility": "Persona resonance model.", "required": ["id"]},
    "APIEndpoint": {"responsibility": "Enforced interface boundary.", "required": ["endpoint_id", "path", "method"]},
    "OpenAPIOperation": {"responsibility": "OpenAPI operation description.", "required": ["operation_id"]},
    "MoStarAPIDoc": {"responsibility": "MoStar API catalog document.", "required": ["id"]},
    "RuntimeEvent": {"responsibility": "Runtime effect emitted by artifact interaction.", "required": ["id", "type", "created_at"]},
    "ExecutionEvent": {"responsibility": "Execution trace event.", "required": ["id", "created_at"]},
    "IntegrityAudit": {"responsibility": "Critical write audit proof.", "required": ["id", "verdict", "created_at"]},
    "CovenantSeal": {"responsibility": "Artifact seal anchor.", "required": ["id", "sealed_at"]},
}

CANONICAL_RELATIONSHIPS = [
    ("MoStarMoment", "HAS_PERSONA", "Persona"),
    ("MoStarMoment", "HAS_LIFESTAGE", "LifeStage"),
    ("MoStarMoment", "HAS_SIGNATURE", "MoStarSignature"),
    ("MoStarMoment", "SEALED_BY", "CovenantSeal"),
    ("MoStarMoment", "AUDITED_BY", "IntegrityAudit"),
    ("MoStarMoment", "BINDS_LAYER", "SoulLayer|MindLayer|BodyLayer"),
    ("MoStarMoment", "HAS_MEMORY", "Memory|GridKnowledge"),
    ("MoStarMoment", "GOVERNED_BY", "Constraint|UsePolicy|Principle"),
    ("Persona", "HAS_PERSONA_TRAIT", "PersonaTrait"),
    ("Persona", "ALIGNED_WITH_CULTURE", "CultureAnchor"),
    ("Persona", "REASONS_WITH", "ReasoningFramework"),
    ("Persona", "EXPRESSED_THROUGH", "Interface"),
    ("Persona", "BOUND_BY", "Constraint|Ethic|UsePolicy"),
    ("APIEndpoint", "DESCRIBES", "OpenAPIOperation"),
    ("APIEndpoint", "EXPOSES_INTERFACE", "Interface"),
    ("APIEndpoint", "APPLIES_TO", "CanonicalComponent|MoScript|DecisionIntelligence"),
    ("APIEndpoint", "GOVERNED_BY", "UsePolicy|Constraint"),
    ("APIEndpoint", "EMITS", "RuntimeEvent"),
    ("APIEndpoint", "AUDITS", "IntegrityAudit"),
]


class MomentCreateRequest(BaseModel):
    id: Optional[str] = Field(default=None, min_length=1, max_length=160)
    quantum_id: Optional[str] = Field(default=None, max_length=240)
    source_artifact_ids: list[str] = Field(default_factory=list, max_length=50)
    persona_id: Optional[str] = Field(default=None, max_length=160)
    lifestage_key: Optional[str] = Field(default=None, max_length=160)
    runtime_context: dict[str, Any] = Field(default_factory=dict)
    memory_ids: list[str] = Field(default_factory=list, max_length=50)
    governed_by_ids: list[str] = Field(default_factory=list, max_length=50)
    layers: list[str] = Field(default_factory=list, max_length=3)
    payload: dict[str, Any] = Field(default_factory=dict)
    created_by: str = Field(default="api", max_length=160)


class PersonaActivationRequest(BaseModel):
    activated_by: str = Field(default="api", max_length=160)
    reason: Optional[str] = Field(default=None, max_length=1000)


class GridQueryRequest(BaseModel):
    label: str = Field(..., min_length=1, max_length=80)
    property: str = Field(default="id", min_length=1, max_length=80)
    value: str = Field(..., min_length=1, max_length=500)
    limit: int = Field(default=50, ge=1, le=200)


class InteractionSimulateRequest(BaseModel):
    canonical_id: str = Field(..., min_length=1, max_length=500)
    action: str = Field(..., min_length=1, max_length=120)
    include_neighbors: bool = True
    limit: int = Field(default=50, ge=1, le=200)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _stable_id(prefix: str, payload: dict[str, Any]) -> str:
    body = json.dumps(payload, sort_keys=True, default=str, separators=(",", ":"))
    return f"{prefix}_{hashlib.sha256(body.encode('utf-8')).hexdigest()[:24]}"


def _node(record_value: Any) -> Optional[dict]:
    return dict(record_value) if record_value is not None else None


def _require_driver(request: Request):
    orchestrator = request.app.state.orchestrator
    if not orchestrator.mindgraph.connected or orchestrator.mindgraph._driver is None:
        raise HTTPException(503, "MindGraph not connected")
    return orchestrator.mindgraph._driver


def _validate_token(name: str, value: str) -> str:
    if not value.replace("_", "").isalnum():
        raise HTTPException(400, f"Invalid {name}")
    return value


@router.get("/mostar/schema")
async def canonical_schema():
    return {
        "nodes": CANONICAL_NODE_TYPES,
        "relationships": [
            {"from": src, "type": rel, "to": dst}
            for src, rel, dst in CANONICAL_RELATIONSHIPS
        ],
        "hardening": [
            "bounded traversals only",
            "parameterized Cypher only",
            "writes emit RuntimeEvent",
            "critical writes emit IntegrityAudit",
            "sealed moments are immutable by contract",
        ],
    }


@router.post("/mostar/moments", status_code=201)
async def create_moment(payload: MomentCreateRequest, request: Request):
    driver = _require_driver(request)
    now = _now()
    moment_id = payload.id or _stable_id(
        "mom",
        {
            "quantum_id": payload.quantum_id,
            "source_artifact_ids": payload.source_artifact_ids,
            "persona_id": payload.persona_id,
            "lifestage_key": payload.lifestage_key,
            "payload": payload.payload,
        },
    )
    quantum_id = payload.quantum_id or moment_id
    seal_id = f"seal_{moment_id}"
    audit_id = f"audit_{moment_id}"
    event_id = f"runtime_{moment_id}"
    props = {
        "id": moment_id,
        "quantum_id": quantum_id,
        "sealed_at": now,
        "mo_processed": True,
        "cluster_id": MOSTAR_CLUSTER_ID,
        "source_artifact_ids": payload.source_artifact_ids,
        "runtime_context": json.dumps(payload.runtime_context, sort_keys=True, default=str),
        "payload": json.dumps(payload.payload, sort_keys=True, default=str),
        "created_by": payload.created_by,
    }

    async with driver.session(database=NEO4J_DATABASE) as session:
        result = await session.run(
            """
            MERGE (m:MoStarMoment {id: $id})
            ON CREATE SET m = $props, m.created_at = $now
            ON MATCH SET m.last_seen_at = $now
            WITH m
            MERGE (seal:CovenantSeal {id: $seal_id})
              ON CREATE SET seal.sealed_at = $now, seal.kind = 'moment', seal.glyph = $seal
            MERGE (audit:IntegrityAudit {id: $audit_id})
              ON CREATE SET audit.created_at = $now, audit.verdict = 'accepted',
                            audit.scope = 'moment_creation', audit.cluster_id = $cluster_id
            MERGE (evt:RuntimeEvent {id: $event_id})
              ON CREATE SET evt.created_at = $now, evt.type = 'MOSTAR_MOMENT_CREATED',
                            evt.source = 'mostar_artifacts_api', evt.cluster_id = $cluster_id
            MERGE (m)-[:SEALED_BY]->(seal)
            MERGE (m)-[:AUDITED_BY]->(audit)
            MERGE (m)-[:EMITTED_EVENT]->(evt)
            WITH m, seal, audit, evt
            FOREACH (persona_id IN CASE WHEN $persona_id IS NULL THEN [] ELSE [$persona_id] END |
              MERGE (p:Persona {id: persona_id})
              MERGE (m)-[:HAS_PERSONA]->(p)
            )
            FOREACH (lifestage_key IN CASE WHEN $lifestage_key IS NULL THEN [] ELSE [$lifestage_key] END |
              MERGE (ls:LifeStage {key: lifestage_key})
              ON CREATE SET ls.name = lifestage_key
              MERGE (m)-[:HAS_LIFESTAGE]->(ls)
            )
            FOREACH (memory_id IN $memory_ids |
              MERGE (mem:Memory {id: memory_id})
              MERGE (m)-[:HAS_MEMORY]->(mem)
            )
            FOREACH (policy_id IN $governed_by_ids |
              MERGE (policy:UsePolicy {id: policy_id})
              MERGE (m)-[:GOVERNED_BY]->(policy)
            )
            FOREACH (layer_name IN $layers |
              MERGE (layer:CanonicalLayer {name: layer_name})
              MERGE (m)-[:BINDS_LAYER]->(layer)
            )
            RETURN m, seal, audit, evt
            """,
            id=moment_id,
            props=props,
            now=now,
            seal_id=seal_id,
            audit_id=audit_id,
            event_id=event_id,
            seal=SEAL_GLYPH,
            cluster_id=MOSTAR_CLUSTER_ID,
            persona_id=payload.persona_id,
            lifestage_key=payload.lifestage_key,
            memory_ids=payload.memory_ids,
            governed_by_ids=payload.governed_by_ids,
            layers=payload.layers,
        )
        record = await result.single()

    return {
        "moment": _node(record["m"]),
        "seal": _node(record["seal"]),
        "audit": _node(record["audit"]),
        "runtime_event": _node(record["evt"]),
        "provenance_handle": moment_id,
    }


@router.get("/mostar/moments/{moment_id}")
async def get_moment(moment_id: str, request: Request):
    driver = _require_driver(request)
    async with driver.session(database=NEO4J_DATABASE) as session:
        result = await session.run(
            """
            MATCH (m:MoStarMoment {id: $id})
            OPTIONAL MATCH (m)-[:HAS_PERSONA]->(p)
            OPTIONAL MATCH (m)-[:HAS_LIFESTAGE]->(ls:LifeStage)
            OPTIONAL MATCH (m)-[:HAS_SIGNATURE]->(sig:MoStarSignature)
            OPTIONAL MATCH (m)-[:SEALED_BY]->(seal:CovenantSeal)
            OPTIONAL MATCH (m)-[:AUDITED_BY]->(audit:IntegrityAudit)
            RETURN m, p, ls, sig, seal, audit
            """,
            id=moment_id,
        )
        record = await result.single()
    if not record:
        raise HTTPException(404, f"MoStarMoment {moment_id} not found")
    return {key: _node(record[key]) for key in record.keys()}


@router.get("/mostar/moments/{moment_id}/context")
async def get_moment_context(moment_id: str, request: Request):
    driver = _require_driver(request)
    async with driver.session(database=NEO4J_DATABASE) as session:
        result = await session.run(
            """
            MATCH (m:MoStarMoment {id: $id})
            OPTIONAL MATCH (m)-[:HAS_PERSONA]->(p:Persona)
            OPTIONAL MATCH (p)-[:HAS_PERSONA_TRAIT]->(t:PersonaTrait)
            OPTIONAL MATCH (p)-[:REASONS_WITH]->(rf:ReasoningFramework)
            OPTIONAL MATCH (m)-[:HAS_LIFESTAGE]->(ls:LifeStage)
            OPTIONAL MATCH (ls)-[:HAS_STAGE_PROFILE]->(sp:StageProfile)
            OPTIONAL MATCH (sp)-[:HAS_FEATURE]->(sf)
            OPTIONAL MATCH (m)-[:HAS_MEMORY]->(mem)
            RETURN m, p, ls, sp,
                   collect(DISTINCT t) AS traits,
                   collect(DISTINCT rf) AS frameworks,
                   collect(DISTINCT sf) AS stage_features,
                   collect(DISTINCT mem) AS memories
            """,
            id=moment_id,
        )
        record = await result.single()
    if not record:
        raise HTTPException(404, f"MoStarMoment {moment_id} not found")
    return {
        "moment": _node(record["m"]),
        "persona": _node(record["p"]),
        "lifestage": _node(record["ls"]),
        "stage_profile": _node(record["sp"]),
        "traits": [_node(item) for item in record["traits"]],
        "frameworks": [_node(item) for item in record["frameworks"]],
        "stage_features": [_node(item) for item in record["stage_features"]],
        "memories": [_node(item) for item in record["memories"]],
    }


@router.get("/mostar/moments/{moment_id}/lineage")
async def get_moment_lineage(moment_id: str, request: Request, limit: int = 100):
    driver = _require_driver(request)
    limit = min(max(limit, 1), 200)
    async with driver.session(database=NEO4J_DATABASE) as session:
        result = await session.run(
            """
            MATCH (m:MoStarMoment {id: $id})
            OPTIONAL MATCH (m)-[r]-(adj)
            RETURN type(r) AS rel_type, labels(adj) AS labels, adj
            LIMIT $limit
            """,
            id=moment_id,
            limit=limit,
        )
        records = await result.data()
    return {
        "moment_id": moment_id,
        "neighbors": [
            {"rel_type": row["rel_type"], "labels": row["labels"], "node": _node(row["adj"])}
            for row in records
            if row["adj"] is not None
        ],
    }


@router.get("/lifestages")
async def list_lifestages(request: Request, limit: int = 100):
    driver = _require_driver(request)
    async with driver.session(database=NEO4J_DATABASE) as session:
        result = await session.run(
            "MATCH (ls:LifeStage) RETURN ls ORDER BY coalesce(ls.order, 999), coalesce(ls.name, ls.key) LIMIT $limit",
            limit=min(max(limit, 1), 200),
        )
        records = await result.data()
    return {"lifestages": [_node(row["ls"]) for row in records]}


@router.get("/lifestages/{key}")
async def get_lifestage(key: str, request: Request):
    driver = _require_driver(request)
    async with driver.session(database=NEO4J_DATABASE) as session:
        result = await session.run("MATCH (ls:LifeStage {key: $key}) RETURN ls", key=key)
        record = await result.single()
    if not record:
        raise HTTPException(404, f"LifeStage {key} not found")
    return {"lifestage": _node(record["ls"])}


@router.get("/lifestages/{key}/profile")
async def get_lifestage_profile(key: str, request: Request):
    driver = _require_driver(request)
    async with driver.session(database=NEO4J_DATABASE) as session:
        result = await session.run(
            """
            MATCH (ls:LifeStage {key: $key})
            OPTIONAL MATCH (ls)-[:HAS_STAGE_PROFILE]->(sp:StageProfile)
            RETURN ls, sp
            """,
            key=key,
        )
        record = await result.single()
    if not record:
        raise HTTPException(404, f"LifeStage {key} not found")
    return {"lifestage": _node(record["ls"]), "profile": _node(record["sp"])}


@router.get("/lifestages/{key}/features")
async def get_lifestage_features(key: str, request: Request):
    driver = _require_driver(request)
    async with driver.session(database=NEO4J_DATABASE) as session:
        result = await session.run(
            """
            MATCH (ls:LifeStage {key: $key})
            OPTIONAL MATCH (ls)-[:HAS_STAGE_PROFILE]->(:StageProfile)-[:HAS_FEATURE]->(f)
            RETURN collect(DISTINCT f) AS features
            """,
            key=key,
        )
        record = await result.single()
    if not record:
        raise HTTPException(404, f"LifeStage {key} not found")
    return {"key": key, "features": [_node(item) for item in record["features"] if item is not None]}


@router.get("/personas/{persona_id}")
async def get_persona(persona_id: str, request: Request):
    driver = _require_driver(request)
    async with driver.session(database=NEO4J_DATABASE) as session:
        result = await session.run("MATCH (p:Persona {id: $id}) RETURN p", id=persona_id)
        record = await result.single()
    if not record:
        raise HTTPException(404, f"Persona {persona_id} not found")
    return {"persona": _node(record["p"])}


@router.get("/personas/{persona_id}/context")
async def get_persona_context(persona_id: str, request: Request):
    driver = _require_driver(request)
    async with driver.session(database=NEO4J_DATABASE) as session:
        result = await session.run(
            """
            MATCH (p:Persona {id: $id})
            OPTIONAL MATCH (p)-[:HAS_PERSONA_TRAIT]->(t:PersonaTrait)
            OPTIONAL MATCH (p)-[:REASONS_WITH]->(rf:ReasoningFramework)
            OPTIONAL MATCH (p)-[:ALIGNED_WITH_CULTURE]->(ca:CultureAnchor)
            OPTIONAL MATCH (p)-[:EXPRESSED_THROUGH]->(i:Interface)
            OPTIONAL MATCH (p)-[:BOUND_BY]->(b)
            RETURN p, collect(DISTINCT t) AS traits,
                   collect(DISTINCT rf) AS frameworks,
                   collect(DISTINCT ca) AS culture,
                   collect(DISTINCT i) AS interfaces,
                   collect(DISTINCT b) AS bounds
            """,
            id=persona_id,
        )
        record = await result.single()
    if not record:
        raise HTTPException(404, f"Persona {persona_id} not found")
    return {
        "persona": _node(record["p"]),
        "traits": [_node(item) for item in record["traits"]],
        "frameworks": [_node(item) for item in record["frameworks"]],
        "culture": [_node(item) for item in record["culture"]],
        "interfaces": [_node(item) for item in record["interfaces"]],
        "bounds": [_node(item) for item in record["bounds"]],
    }


@router.post("/personas/{persona_id}/activate")
async def activate_persona(persona_id: str, payload: PersonaActivationRequest, request: Request):
    driver = _require_driver(request)
    now = _now()
    activation_id = f"persona_activation_{persona_id}_{uuid.uuid4().hex[:12]}"
    async with driver.session(database=NEO4J_DATABASE) as session:
        result = await session.run(
            """
            MATCH (p:Persona {id: $id})
            SET p.active = true, p.active_version = coalesce(p.active_version, 0) + 1,
                p.activated_at = $now, p.activated_by = $activated_by
            CREATE (evt:RuntimeEvent {
                id: $activation_id,
                type: 'PERSONA_ACTIVATED',
                persona_id: $id,
                reason: $reason,
                created_at: $now,
                cluster_id: $cluster_id
            })
            CREATE (p)-[:EMITTED_EVENT]->(evt)
            RETURN p, evt
            """,
            id=persona_id,
            now=now,
            activated_by=payload.activated_by,
            reason=payload.reason,
            activation_id=activation_id,
            cluster_id=MOSTAR_CLUSTER_ID,
        )
        record = await result.single()
    if not record:
        raise HTTPException(404, f"Persona {persona_id} not found")
    return {"persona": _node(record["p"]), "runtime_event": _node(record["evt"])}


@router.get("/personas/{persona_id}/resonance")
async def get_persona_resonance(persona_id: str, request: Request):
    driver = _require_driver(request)
    async with driver.session(database=NEO4J_DATABASE) as session:
        result = await session.run(
            """
            MATCH (p:Persona {id: $id})
            OPTIONAL MATCH (p)-[:HAS_RESONANCE_PROFILE]->(rp:ResonanceProfile)
            RETURN p, rp
            """,
            id=persona_id,
        )
        record = await result.single()
    if not record:
        raise HTTPException(404, f"Persona {persona_id} not found")
    return {"persona": _node(record["p"]), "resonance": _node(record["rp"])}


@router.get("/api/endpoints")
async def list_api_endpoints(request: Request, limit: int = 100):
    driver = _require_driver(request)
    async with driver.session(database=NEO4J_DATABASE) as session:
        result = await session.run(
            """
            MATCH (e:APIEndpoint)
            RETURN e
            ORDER BY coalesce(e.path, e.endpoint_id)
            LIMIT $limit
            """,
            limit=min(max(limit, 1), 200),
        )
        records = await result.data()
    return {"endpoints": [_node(row["e"]) for row in records]}


@router.get("/api/endpoints/{endpoint_id}")
async def get_api_endpoint(endpoint_id: str, request: Request):
    driver = _require_driver(request)
    async with driver.session(database=NEO4J_DATABASE) as session:
        result = await session.run(
            """
            MATCH (e:APIEndpoint {endpoint_id: $id})
            OPTIONAL MATCH (e)-[:DESCRIBES]->(op:OpenAPIOperation)
            OPTIONAL MATCH (e)-[:GOVERNED_BY]->(policy)
            OPTIONAL MATCH (e)-[:APPLIES_TO]->(component)
            RETURN e, collect(DISTINCT op) AS operations,
                   collect(DISTINCT policy) AS policies,
                   collect(DISTINCT component) AS components
            """,
            id=endpoint_id,
        )
        record = await result.single()
    if not record:
        raise HTTPException(404, f"APIEndpoint {endpoint_id} not found")
    return {
        "endpoint": _node(record["e"]),
        "operations": [_node(item) for item in record["operations"]],
        "policies": [_node(item) for item in record["policies"]],
        "components": [_node(item) for item in record["components"]],
    }


@router.get("/api/components/{canonical_id}/interfaces")
async def get_component_interfaces(canonical_id: str, request: Request):
    driver = _require_driver(request)
    async with driver.session(database=NEO4J_DATABASE) as session:
        result = await session.run(
            """
            MATCH (c {canonical_id: $canonical_id})
            OPTIONAL MATCH (e:APIEndpoint)-[:APPLIES_TO]->(c)
            OPTIONAL MATCH (e)-[:EXPOSES_INTERFACE]->(i:Interface)
            RETURN c, collect(DISTINCT e) AS endpoints, collect(DISTINCT i) AS interfaces
            LIMIT 1
            """,
            canonical_id=canonical_id,
        )
        record = await result.single()
    if not record:
        raise HTTPException(404, f"Canonical component {canonical_id} not found")
    return {
        "component": _node(record["c"]),
        "endpoints": [_node(item) for item in record["endpoints"]],
        "interfaces": [_node(item) for item in record["interfaces"]],
    }


@router.get("/grid/entities/{canonical_id}/neighbors")
async def get_entity_neighbors(canonical_id: str, request: Request, limit: int = 100):
    driver = _require_driver(request)
    async with driver.session(database=NEO4J_DATABASE) as session:
        result = await session.run(
            """
            MATCH (n {canonical_id: $canonical_id})
            OPTIONAL MATCH (n)-[r]-(adj)
            RETURN n, type(r) AS relType, labels(adj) AS adjLabels, adj
            LIMIT $limit
            """,
            canonical_id=canonical_id,
            limit=min(max(limit, 1), 200),
        )
        records = await result.data()
    if not records:
        raise HTTPException(404, f"Entity {canonical_id} not found")
    return {
        "canonical_id": canonical_id,
        "entity": _node(records[0]["n"]),
        "neighbors": [
            {"rel_type": row["relType"], "labels": row["adjLabels"], "node": _node(row["adj"])}
            for row in records
            if row["adj"] is not None
        ],
    }


@router.get("/grid/moments/{moment_id}/impact")
async def get_moment_impact(moment_id: str, request: Request, limit: int = 100):
    driver = _require_driver(request)
    async with driver.session(database=NEO4J_DATABASE) as session:
        result = await session.run(
            """
            MATCH (m:MoStarMoment {id: $id})
            OPTIONAL MATCH (m)-[:HAS_MEMORY|GOVERNED_BY|HAS_PERSONA|HAS_LIFESTAGE|EMITTED_EVENT|AUDITED_BY]-(n)
            RETURN labels(n) AS labels, n
            LIMIT $limit
            """,
            id=moment_id,
            limit=min(max(limit, 1), 200),
        )
        records = await result.data()
    return {
        "moment_id": moment_id,
        "impact": [
            {"labels": row["labels"], "node": _node(row["n"])}
            for row in records
            if row["n"] is not None
        ],
        "recompute": {"queued": False, "mode": "simulation-only"},
    }


@router.post("/grid/query")
async def bounded_grid_query(payload: GridQueryRequest, request: Request):
    label = _validate_token("label", payload.label)
    prop = _validate_token("property", payload.property)
    driver = _require_driver(request)
    async with driver.session(database=NEO4J_DATABASE) as session:
        result = await session.run(
            f"MATCH (n:`{label}`) WHERE n.`{prop}` = $value RETURN n LIMIT $limit",
            value=payload.value,
            limit=payload.limit,
        )
        records = await result.data()
    return {"results": [_node(row["n"]) for row in records], "limit": payload.limit}


@router.post("/grid/interaction/simulate")
async def simulate_interaction(payload: InteractionSimulateRequest, request: Request):
    driver = _require_driver(request)
    neighbors = []
    if payload.include_neighbors:
        async with driver.session(database=NEO4J_DATABASE) as session:
            result = await session.run(
                """
                MATCH (n {canonical_id: $canonical_id})
                OPTIONAL MATCH (n)-[r]-(adj)
                RETURN type(r) AS rel_type, labels(adj) AS labels, adj
                LIMIT $limit
                """,
                canonical_id=payload.canonical_id,
                limit=payload.limit,
            )
            records = await result.data()
        neighbors = [
            {"rel_type": row["rel_type"], "labels": row["labels"], "node": _node(row["adj"])}
            for row in records
            if row["adj"] is not None
        ]

    return {
        "canonical_id": payload.canonical_id,
        "action": payload.action,
        "would_validate": ["UsePolicy", "Constraint"],
        "would_emit": ["RuntimeEvent"],
        "critical_write_would_emit": ["IntegrityAudit"],
        "would_queue_recompute_for": ["GridKnowledge", "Memory", "DecisionIntelligence", "SoulPrint"],
        "neighbors": neighbors,
    }
