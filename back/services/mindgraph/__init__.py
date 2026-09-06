"""
MindGraph — Neo4j Knowledge Graph Interface
Handles all graph reads and writes for the living intelligence.
"""
import asyncio
import json
import logging
import uuid
import grid.config
from datetime import datetime, timezone
from typing import Optional

from neo4j import AsyncGraphDatabase, AsyncDriver, Query
from cypher_guard import GuardedAsyncDriver, CypherGuard
from grid.config import (
    MOSTAR_CLUSTER_ID,
    NEO4J_DATABASE,
    NEO4J_URI,
    NEO4J_USER,
    SEAL_GLYPH,
    get_neo4j_password,
)

logger = logging.getLogger("mindgraph")


class CommitForbiddenError(RuntimeError):
    """Raised when graph writes are attempted outside commit_after_seal."""


class GovernedRetrievalUnavailable(RuntimeError):
    """Raised when Grid-governed context retrieval fails at the infrastructure
    level. Must never be conflated with a successful zero-match retrieval —
    callers rely on this distinction to avoid presenting an ungrounded
    response as Grid-grounded."""


class MindGraph:
    """Sovereign knowledge graph — the Grid's long-term memory."""

    def __init__(self):
        self._driver: Optional[AsyncDriver] = None
        self._active_commit_token: Optional[str] = None

    async def connect(self, retries: int = 5, delay: float = 3.0):
        """Connect to Neo4j, retrying if not ready yet (handles startup race)."""
        for attempt in range(1, retries + 1):
            try:
                raw_driver = AsyncGraphDatabase.driver(
                    NEO4J_URI, auth=(NEO4J_USER, get_neo4j_password())
                )
                await raw_driver.verify_connectivity()
                self._driver = GuardedAsyncDriver(
                    raw_driver,
                    guard=CypherGuard(allow_write=True),
                )
                logger.info("MindGraph connected to Neo4j at %s (attempt %d)", NEO4J_URI, attempt)
                return
            except Exception as e:
                logger.warning("MindGraph connect attempt %d/%d failed: %s", attempt, retries, e)
                if attempt < retries:
                    await asyncio.sleep(delay)
        logger.error("MindGraph could not connect after %d attempts", retries)
        raise RuntimeError(f"MindGraph failed to connect to {NEO4J_URI}")

    async def close(self):
        if self._driver:
            await self._driver.close()

    @property
    def connected(self) -> bool:
        return self._driver is not None

    def begin_commit(self) -> str:
        self._active_commit_token = uuid.uuid4().hex
        return self._active_commit_token

    def end_commit(self, token: str) -> None:
        if token == self._active_commit_token:
            self._active_commit_token = None

    def _assert_commit_token(self, token: str | None) -> None:
        if not token or token != self._active_commit_token:
            raise CommitForbiddenError(
                "mindgraph writes may only be called from commit_after_seal(). "
                "Direct writes are forbidden under Phase 4.0a doctrine."
            )

    # ── Context Retrieval ──────────────────────────────────────────

    async def retrieve_context(self, query: str, limit: int = 10) -> list[dict]:
        """Full-text search for relevant nodes.

        Fails closed: infrastructure failures raise GovernedRetrievalUnavailable
        rather than being conflated with a successful zero-match result. There
        is no unbounded MATCH fallback — a broad, un-ranked graph scan
        presented as retrieval would be a false-grounding risk (see Phase 0
        retrieval incident). If a fallback strategy is needed, it must be
        implemented as an explicit, separately-labeled retrieval_path, not a
        silent substitute for full-text search.
        """
        if not self._driver:
            raise GovernedRetrievalUnavailable("MindGraph has no active driver connection")

        cypher = """
        CALL db.index.fulltext.queryNodes('gridSearch', $query)
        YIELD node, score
        WHERE node.cluster_id = $cluster_id
        RETURN node {.*, _labels: labels(node), _score: score}
        ORDER BY score DESC
        LIMIT $limit
        """
        async with self._driver.session(database=NEO4J_DATABASE) as session:
            try:
                result = await session.run(
                    cypher,
                    query=query,
                    limit=limit,
                    cluster_id=MOSTAR_CLUSTER_ID,
                )
                records = await result.data()
            except Exception as exc:
                logger.exception(
                    "MindGraph retrieval failed",
                    extra={"operation": "retrieve_context"},
                )
                raise GovernedRetrievalUnavailable(
                    f"retrieve_context failed: {type(exc).__name__}: {exc}"
                ) from exc
        return [r["node"] for r in records]

    async def get_agents(self) -> list[dict]:
        """Return all sovereign agents."""
        if not self._driver:
            return []
        cypher = """
        MATCH (a:Agent {cluster_id: $cluster_id})
        RETURN a {.*} AS agent
        ORDER BY a.name
        """
        async with self._driver.session(database=NEO4J_DATABASE) as session:
            result = await session.run(cypher, cluster_id=MOSTAR_CLUSTER_ID)
            return [r["agent"] for r in await result.data()]

    async def get_graph_stats(self) -> dict:
        """Return database-wide graph statistics and the local cluster subset.

        The dashboard's primary counters describe the selected Neo4j database,
        not only records stamped with this runtime's ``cluster_id``.  Keeping the
        cluster counts alongside the database census makes that distinction
        explicit for callers that need sovereign-cluster telemetry.
        """
        if not self._driver:
            return {"status": "disconnected"}
        cypher = """
        CALL {
            MATCH (n) RETURN count(n) AS nodes
        }
        CALL {
            MATCH ()-[r]->() RETURN count(r) AS relationships
        }
        CALL {
            MATCH (n) UNWIND labels(n) AS lbl
            RETURN collect(DISTINCT lbl) AS labels
        }
        CALL {
            MATCH (n {cluster_id: $cluster_id})
            RETURN count(n) AS cluster_nodes
        }
        CALL {
            MATCH (a {cluster_id: $cluster_id})-[r]->(b {cluster_id: $cluster_id})
            RETURN count(r) AS cluster_relationships
        }
        CALL {
            MATCH (n {cluster_id: $cluster_id}) UNWIND labels(n) AS lbl
            RETURN collect(DISTINCT lbl) AS cluster_labels
        }
        RETURN nodes, relationships, labels,
               cluster_nodes, cluster_relationships, cluster_labels
        """
        async with self._driver.session(database=NEO4J_DATABASE) as session:
            result = await session.run(cypher, cluster_id=MOSTAR_CLUSTER_ID)
            record = await result.single()
            if record:
                return {
                    "nodes": record["nodes"],
                    "relationships": record["relationships"],
                    "labels": record["labels"],
                    "scope": "database",
                    "database": NEO4J_DATABASE,
                    "cluster": {
                        "cluster_id": MOSTAR_CLUSTER_ID,
                        "nodes": record["cluster_nodes"],
                        "relationships": record["cluster_relationships"],
                        "labels": record["cluster_labels"],
                    },
                    "status": "connected",
                }
            return {"status": "empty"}

    # ── Knowledge Writing (Learn) ──────────────────────────────────

    async def learn(
        self,
        category: str,
        content: str,
        source_type: str = "runtime_generated",
        verification_status: str = "unverified",
        operational_trust: str = "reference",
        seal: str = "Synthetic",
        source: str = "conversation",
        created_by: str = "grid_orchestrator",
        source_id: str | None = None,
        metadata: dict | None = None,
        _commit_token: str | None = None,
    ) -> str:
        """Write new knowledge to the graph. Returns the node ID."""
        self._assert_commit_token(_commit_token)

        # Provenance Validation
        ALLOWED_SOURCE_TYPES = {"live_api", "human_attested", "imported_archive", "runtime_generated", "seeded_demo", "ai_generated"}
        ALLOWED_VERIFICATION_STATUSES = {"verified", "unverified", "synthetic", "disputed"}
        ALLOWED_OPERATIONAL_TRUSTS = {"operational", "reference", "simulation", "design"}
        ALLOWED_SEALS = {"Operational", "Verified", "Synthetic", "Design"}

        if source_type not in ALLOWED_SOURCE_TYPES:
            raise ValueError(f"Invalid source_type: '{source_type}'. Must be one of {ALLOWED_SOURCE_TYPES}")
        if verification_status not in ALLOWED_VERIFICATION_STATUSES:
            raise ValueError(f"Invalid verification_status: '{verification_status}'. Must be one of {ALLOWED_VERIFICATION_STATUSES}")
        if operational_trust not in ALLOWED_OPERATIONAL_TRUSTS:
            raise ValueError(f"Invalid operational_trust: '{operational_trust}'. Must be one of {ALLOWED_OPERATIONAL_TRUSTS}")
        if seal not in ALLOWED_SEALS:
            raise ValueError(f"Invalid seal: '{seal}'. Must be one of {ALLOWED_SEALS}")

        if not self._driver:
            return "no_connection"

        node_id = f"mem_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S_%f')}"
        props = {
            "id": node_id,
            "content": content,
            "category": category,
            "source": source,
            "source_id": source_id,
            "created_by": created_by,
            "cluster_id": MOSTAR_CLUSTER_ID,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "seal": seal,
            "source_type": source_type,
            "verification_status": verification_status,
            "operational_trust": operational_trust
        }
        if metadata:
            props["metadata"] = json.dumps(metadata)

        cypher = """
        CREATE (m:Memory:GridKnowledge {
            id: $props.id,
            content: $props.content,
            category: $props.category,
            source: $props.source,
            source_id: $props.source_id,
            created_by: $props.created_by,
            cluster_id: $props.cluster_id,
            created_at: $props.created_at,
            seal: $props.seal,
            source_type: $props.source_type,
            verification_status: $props.verification_status,
            operational_trust: $props.operational_trust
        })
        RETURN m.id AS id
        """
        async with self._driver.session(database=NEO4J_DATABASE) as session:
            result = await session.run(cypher, props=props)
            record = await result.single()
            logger.info("Learned: %s → %s", category, node_id)
            return record["id"] if record else node_id

    # ── MoStar Moment (Remember) ──────────────────────────────────

    async def stamp_moment(
        self,
        talk_input: str,
        think_output: str,
        memory_id: str,
        source_type: str = "runtime_generated",
        verification_status: str = "unverified",
        operational_trust: str = "reference",
        seal: str = "Synthetic",
        source: str = "conversation",
        created_by: str = "grid_orchestrator",
        _commit_token: str | None = None,
    ) -> str:
        """Seal a Talk→Learn→Remember cycle as a MoStarMoment."""
        self._assert_commit_token(_commit_token)

        # Provenance Validation
        ALLOWED_SOURCE_TYPES = {"live_api", "human_attested", "imported_archive", "runtime_generated", "seeded_demo", "ai_generated"}
        ALLOWED_VERIFICATION_STATUSES = {"verified", "unverified", "synthetic", "disputed"}
        ALLOWED_OPERATIONAL_TRUSTS = {"operational", "reference", "simulation", "design"}
        ALLOWED_SEALS = {"Operational", "Verified", "Synthetic", "Design"}

        if source_type not in ALLOWED_SOURCE_TYPES:
            raise ValueError(f"Invalid source_type: '{source_type}'. Must be one of {ALLOWED_SOURCE_TYPES}")
        if verification_status not in ALLOWED_VERIFICATION_STATUSES:
            raise ValueError(f"Invalid verification_status: '{verification_status}'. Must be one of {ALLOWED_VERIFICATION_STATUSES}")
        if operational_trust not in ALLOWED_OPERATIONAL_TRUSTS:
            raise ValueError(f"Invalid operational_trust: '{operational_trust}'. Must be one of {ALLOWED_OPERATIONAL_TRUSTS}")
        if seal not in ALLOWED_SEALS:
            raise ValueError(f"Invalid seal: '{seal}'. Must be one of {ALLOWED_SEALS}")

        if not self._driver:
            return "no_connection"

        moment_id = f"moment_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S_%f')}"
        cypher = """
        CREATE (m:MoStarMoment {
            id: $moment_id,
            talk_input: $talk_input,
            think_output: $think_output,
            cluster_id: $cluster_id,
            sealed_at: $sealed_at,
            seal: $seal,
            source: $source,
            created_by: $created_by,
            source_type: $source_type,
            verification_status: $verification_status,
            operational_trust: $operational_trust
        })
        WITH m
        OPTIONAL MATCH (mem:Memory {id: $memory_id})
        FOREACH (_ IN CASE WHEN mem IS NOT NULL THEN [1] ELSE [] END |
            CREATE (m)-[:SEALED_FROM]->(mem)
        )
        RETURN m.id AS id
        """
        async with self._driver.session(database=NEO4J_DATABASE) as session:
            result = await session.run(cypher,
                moment_id=moment_id,
                talk_input=talk_input[:500],
                think_output=think_output[:500],
                memory_id=memory_id,
                cluster_id=MOSTAR_CLUSTER_ID,
                sealed_at=datetime.now(timezone.utc).isoformat(),
                seal=seal,
                source=source,
                created_by=created_by,
                source_type=source_type,
                verification_status=verification_status,
                operational_trust=operational_trust
            )
            record = await result.single()
            logger.info("MoStarMoment sealed: %s %s", moment_id, seal)
            return record["id"] if record else moment_id

    # ── Schema Bootstrap ──────────────────────────────────────────

    async def ensure_schema(self):
        """Create indexes and constraints if they don't exist."""
        if not self._driver:
            return
        commands = [
            "CREATE CONSTRAINT agent_id IF NOT EXISTS FOR (a:Agent) REQUIRE a.id IS UNIQUE",
            "CREATE CONSTRAINT memory_id IF NOT EXISTS FOR (m:Memory) REQUIRE m.id IS UNIQUE",
            "CREATE CONSTRAINT moment_id IF NOT EXISTS FOR (m:MoStarMoment) REQUIRE m.id IS UNIQUE",
            "CREATE INDEX cluster_id IF NOT EXISTS FOR (n:GridKnowledge) ON (n.cluster_id)",
            "CREATE INDEX memory_category IF NOT EXISTS FOR (m:Memory) ON (m.category)",
            "CREATE INDEX moment_sealed IF NOT EXISTS FOR (m:MoStarMoment) ON (m.sealed_at)",
        ]
        # Fulltext index — separate try since syntax differs
        ft = """
        CREATE FULLTEXT INDEX gridSearch IF NOT EXISTS
        FOR (n:Memory|Agent|MoStarMoment|GridKnowledge)
        ON EACH [n.content, n.name, n.category, n.id]
        """
        async with self._driver.session(database=NEO4J_DATABASE) as session:
            for cmd in commands:
                try:
                    await session.run(Query(cmd))
                except Exception as e:
                    logger.debug("Schema command skipped: %s", e)
            try:
                await session.run(ft)
            except Exception as e:
                logger.debug("Fulltext index skipped: %s", e)
        logger.info("MindGraph schema ensured")
