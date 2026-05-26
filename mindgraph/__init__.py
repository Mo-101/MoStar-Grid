"""
MindGraph — Neo4j Knowledge Graph Interface
Handles all graph reads and writes for the living intelligence.
"""
import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Optional
from contextlib import asynccontextmanager

from neo4j import AsyncGraphDatabase, AsyncDriver
from grid.config import NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD, NEO4J_DATABASE, SEAL_GLYPH

logger = logging.getLogger("mindgraph")


class CommitForbiddenError(RuntimeError):
    """Raised when graph writes are attempted outside commit_after_seal."""


class MindGraph:
    """Sovereign knowledge graph — the Grid's long-term memory."""

    def __init__(self):
        self._driver: Optional[AsyncDriver] = None
        self._active_commit_token: Optional[str] = None

    async def connect(self):
        self._driver = AsyncGraphDatabase.driver(
            NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD)
        )
        try:
            await self._driver.verify_connectivity()
            logger.info("MindGraph connected to Neo4j at %s", NEO4J_URI)
        except Exception as e:
            logger.error("MindGraph connection failed: %s", e)
            self._driver = None
            raise

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
        """Full-text + label search for relevant nodes."""
        if not self._driver:
            return []

        cypher = """
        CALL db.index.fulltext.queryNodes('gridSearch', $query)
        YIELD node, score
        RETURN node {.*, _labels: labels(node), _score: score}
        ORDER BY score DESC
        LIMIT $limit
        """
        # Fallback if fulltext index doesn't exist yet
        fallback = """
        MATCH (n)
        WHERE any(prop IN keys(n) WHERE toString(n[prop]) CONTAINS $query)
        RETURN n {.*, _labels: labels(n), _score: 1.0} AS node
        LIMIT $limit
        """
        async with self._driver.session(database=NEO4J_DATABASE) as session:
            try:
                result = await session.run(cypher, query=query, limit=limit)
                records = await result.data()
                if records:
                    return [r["node"] for r in records]
            except Exception:
                pass

            try:
                result = await session.run(fallback, query=query, limit=limit)
                records = await result.data()
                return [r["node"] for r in records]
            except Exception as e:
                logger.warning("Context retrieval failed: %s", e)
                return []

    async def get_agents(self) -> list[dict]:
        """Return all sovereign agents."""
        if not self._driver:
            return []
        cypher = "MATCH (a:Agent) RETURN a {.*} AS agent ORDER BY a.name"
        async with self._driver.session(database=NEO4J_DATABASE) as session:
            result = await session.run(cypher)
            return [r["agent"] for r in await result.data()]

    async def get_graph_stats(self) -> dict:
        """Basic graph statistics."""
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
        RETURN nodes, relationships, labels
        """
        async with self._driver.session(database=NEO4J_DATABASE) as session:
            result = await session.run(cypher)
            record = await result.single()
            if record:
                return {
                    "nodes": record["nodes"],
                    "relationships": record["relationships"],
                    "labels": record["labels"],
                    "status": "connected",
                }
            return {"status": "empty"}

    # ── Knowledge Writing (Learn) ──────────────────────────────────

    async def learn(
        self,
        category: str,
        content: str,
        source: str = "conversation",
        metadata: dict = None,
        _commit_token: str = None,
    ) -> str:
        """Write new knowledge to the graph. Returns the node ID."""
        self._assert_commit_token(_commit_token)
        if not self._driver:
            return "no_connection"

        node_id = f"mem_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S_%f')}"
        props = {
            "id": node_id,
            "content": content,
            "category": category,
            "source": source,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "seal": SEAL_GLYPH,
        }
        if metadata:
            props["metadata"] = json.dumps(metadata)

        cypher = """
        CREATE (m:Memory:GridKnowledge {
            id: $props.id,
            content: $props.content,
            category: $props.category,
            source: $props.source,
            created_at: $props.created_at,
            seal: $props.seal
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
        _commit_token: str = None,
    ) -> str:
        """Seal a Talk→Learn→Remember cycle as a MoStarMoment."""
        self._assert_commit_token(_commit_token)
        if not self._driver:
            return "no_connection"

        moment_id = f"moment_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S_%f')}"
        cypher = """
        CREATE (m:MoStarMoment {
            id: $moment_id,
            talk_input: $talk_input,
            think_output: $think_output,
            sealed_at: $sealed_at,
            seal: $seal
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
                sealed_at=datetime.now(timezone.utc).isoformat(),
                seal=SEAL_GLYPH,
            )
            record = await result.single()
            logger.info("MoStarMoment sealed: %s %s", moment_id, SEAL_GLYPH)
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
                    await session.run(cmd)
                except Exception as e:
                    logger.debug("Schema command skipped: %s", e)
            try:
                await session.run(ft)
            except Exception as e:
                logger.debug("Fulltext index skipped: %s", e)
        logger.info("MindGraph schema ensured")
