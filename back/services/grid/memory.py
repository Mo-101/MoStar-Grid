import logging
from datetime import datetime, timedelta, timezone
from grid.config import MOSTAR_CLUSTER_ID

logger = logging.getLogger("grid_memory")

NEO4J_DATABASE = "neo4j"

class MemoryLayer:
    def __init__(self, mindgraph):
        self.mindgraph = mindgraph

    async def log_event(self, event) -> str:
        """Write a GridEvent to Neo4j."""
        if not self.mindgraph.connected:
            logger.warning("MindGraph not connected, skipping memory write.")
            return ""

        try:
            # Ensure MoStarGrid node exists
            async with self.mindgraph._driver.session(database=NEO4J_DATABASE) as session:
                await session.run(
                    "MERGE (grid:MoStarGrid {cluster_id: $cluster_id})",
                    cluster_id=MOSTAR_CLUSTER_ID
                )

                result = await session.run(
                    """
                    CREATE (e:GridEvent {
                        id: $id,
                        type: $type,
                        severity: $severity,
                        mood: $mood,
                        source: $source,
                        source_id: $source_id,
                        created_by: $created_by,
                        text: $text,
                        created_at: $created_at,
                        cluster_id: $cluster_id,
                        source_type: $source_type,
                        verification_status: $verification_status,
                        operational_trust: $operational_trust,
                        seal: $seal
                    })
                    WITH e
                    MATCH (grid:MoStarGrid {cluster_id: $cluster_id})
                    CREATE (e)-[:OBSERVED_BY]->(grid)
                    RETURN e.id AS id
                    """,
                    id=event.id,
                    type=event.type,
                    severity=event.severity,
                    mood=event.mood,
                    source=event.source,
                    source_id=event.source_id,
                    created_by=event.created_by,
                    text=event.text,
                    created_at=event.created_at,
                    source_type=event.source_type,
                    verification_status=event.verification_status,
                    operational_trust=event.operational_trust,
                    seal="Operational" if event.operational_trust == "operational" else "Synthetic",
                    cluster_id=MOSTAR_CLUSTER_ID
                )
                record = await result.single()
                return record["id"] if record else ""
        except Exception as e:
            logger.error(f"Failed to write event memory: {e}")
            return ""

    async def log_briefing(self, event, raw_telemetry: dict, raw_signals: str) -> str:
        """Write a BriefingLog to Neo4j and connect it to the GridEvent."""
        if not self.mindgraph.connected:
            return ""

        try:
            async with self.mindgraph._driver.session(database=NEO4J_DATABASE) as session:
                result = await session.run(
                    """
                    MATCH (e:GridEvent {id: $event_id})
                    CREATE (b:BriefingLog {
                        id: $b_id,
                        created_at: $created_at,
                        cluster_id: $cluster_id,
                        source: 'briefing_generator',
                        created_by: 'autonomous_announcer',
                        source_type: 'ai_generated',
                        verification_status: 'unverified',
                        operational_trust: 'reference',
                        seal: 'Synthetic'
                    })
                    CREATE (b)-[:EMITTED]->(e)
                    RETURN b.id AS id
                    """,
                    event_id=event.id,
                    b_id=f"brief_{event.id}",
                    created_at=event.created_at,
                    cluster_id=MOSTAR_CLUSTER_ID
                )
                record = await result.single()
                return record["id"] if record else ""
        except Exception as e:
            logger.error(f"Failed to write briefing memory: {e}")
            return ""

    async def log_woo_utterance(self, event, audio_url: str) -> str:
        """Write a WooUtterance to Neo4j and connect it to the GridEvent."""
        if not self.mindgraph.connected:
            return ""

        try:
            async with self.mindgraph._driver.session(database=NEO4J_DATABASE) as session:
                result = await session.run(
                    """
                    MATCH (e:GridEvent {id: $event_id})
                    CREATE (w:WooUtterance {
                        id: $w_id,
                        audio_url: $audio_url,
                        created_at: $created_at,
                        cluster_id: $cluster_id,
                        source: 'woo_voice',
                        created_by: 'woo',
                        source_type: 'ai_generated',
                        verification_status: 'unverified',
                        operational_trust: 'reference',
                        seal: 'Synthetic'
                    })
                    CREATE (w)-[:RESPONDED_TO]->(e)
                    RETURN w.id AS id
                    """,
                    event_id=event.id,
                    w_id=f"woo_{event.id}",
                    audio_url=audio_url,
                    created_at=event.created_at,
                    cluster_id=MOSTAR_CLUSTER_ID
                )
                record = await result.single()
                return record["id"] if record else ""
        except Exception as e:
            logger.error(f"Failed to write woo utterance: {e}")
            return ""


# ─────────────────────────────────────────────────────────────────────────
# SCHEMA CONSTANTS — adjust after discovery query if names differ
# ─────────────────────────────────────────────────────────────────────────

EVENT_TYPE_EXPR = "coalesce(e.type, e.event_type, e.category, e.classification, 'unknown')"
EVENT_CONTENT_EXPR = "coalesce(e.text, e.content, e.description, e.data, '')"
EVENT_CLUSTER_EXPR = "coalesce(e.cluster_id, e.cluster, 'unknown')"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _cutoff_iso(hours: int) -> str:
    return (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()


# ─────────────────────────────────────────────────────────────────────────
# 1. RECENT MEMORY — last N events + utterances
# ─────────────────────────────────────────────────────────────────────────

async def get_recent_memory(driver, limit: int = 10) -> dict:
    async with driver.session(database=NEO4J_DATABASE) as session:
        result_events = await session.run(f"""
            MATCH (e:GridEvent)
            RETURN {EVENT_TYPE_EXPR} AS type,
                   {EVENT_CLUSTER_EXPR} AS cluster,
                   {EVENT_CONTENT_EXPR} AS content,
                   e.created_at AS created_at
            ORDER BY e.created_at DESC LIMIT $limit
        """, limit=limit)
        events = await result_events.data()

        result_utterances = await session.run("""
            MATCH (w:WooUtterance)
            OPTIONAL MATCH (w)-[:RESPONDED_TO]->(e:GridEvent)
            RETURN coalesce(w.content, w.text, w.message, e.text, '') AS content,
                   w.created_at AS created_at
            ORDER BY w.created_at DESC LIMIT $limit
        """, limit=limit)
        utterances = await result_utterances.data()

    return {
        "events": events,
        "utterances": utterances,
        "retrieved_at": _now_iso(),
    }


# ─────────────────────────────────────────────────────────────────────────
# 2. RECALL — find past events similar to a given type ("I remember...")
# ─────────────────────────────────────────────────────────────────────────

async def recall_similar(driver, event_type: str, hours: int = 24) -> dict:
    async with driver.session(database=NEO4J_DATABASE) as session:
        result = await session.run(f"""
            MATCH (e:GridEvent)
            WHERE {EVENT_TYPE_EXPR} = $event_type
              AND e.created_at >= $cutoff
            RETURN count(e) AS occurrences,
                   collect(DISTINCT {EVENT_CLUSTER_EXPR}) AS clusters,
                   min(e.created_at) AS first_seen,
                   max(e.created_at) AS last_seen
        """, event_type=event_type, cutoff=_cutoff_iso(hours))
        record = await result.single()

    if not record or record["occurrences"] == 0:
        return {"event_type": event_type, "occurrences": 0, "remembered": False}

    return {
        "event_type": event_type,
        "occurrences": record["occurrences"],
        "clusters": record["clusters"],
        "first_seen": record["first_seen"],
        "last_seen": record["last_seen"],
        "remembered": True,
    }


# ─────────────────────────────────────────────────────────────────────────
# 3. CONTINUITY — compare current state to the last briefing
# ─────────────────────────────────────────────────────────────────────────

async def get_last_briefing(session):
    result = await session.run("""
        MATCH (b:BriefingLog)
        WHERE b.event_count IS NOT NULL
        RETURN coalesce(b.message, b.content, b.text, '') AS message,
               b.created_at AS created_at,
               coalesce(b.event_count, 0) AS event_count,
               coalesce(b.node_count, 0) AS node_count,
               coalesce(b.relationship_count, 0) AS relationship_count
        ORDER BY b.created_at DESC LIMIT 1
    """)
    rec = await result.single()
    return dict(rec) if rec else None


async def compute_continuity(driver, window_hours: int = 6) -> dict:
    cutoff = _cutoff_iso(window_hours)
    async with driver.session(database=NEO4J_DATABASE) as session:
        last_briefing = await get_last_briefing(session)

        result_events = await session.run(
            "MATCH (e:GridEvent) RETURN count(e) AS c"
        )
        current_events = (await result_events.single())["c"]

        # Node and Relationship count (general census counts)
        result_nodes = await session.run("MATCH (n) RETURN count(n) AS c")
        current_nodes = (await result_nodes.single())["c"]

        result_rels = await session.run("MATCH ()-[r]->() RETURN count(r) AS c")
        current_relationships = (await result_rels.single())["c"]

        # Repeated signals in the window
        result_types = await session.run(f"""
            MATCH (e:GridEvent)
            WHERE e.created_at >= $cutoff
            RETURN {EVENT_TYPE_EXPR} AS type, count(e) AS count
            ORDER BY count DESC LIMIT 10
        """, cutoff=cutoff)
        type_counts = await result_types.data()

        # Per-cluster activity in the window
        result_clusters = await session.run(f"""
            MATCH (e:GridEvent)
            WHERE e.created_at >= $cutoff
            RETURN {EVENT_CLUSTER_EXPR} AS cluster, count(e) AS count
            ORDER BY count DESC
        """, cutoff=cutoff)
        cluster_activity = await result_clusters.data()

    facts = {
        "current_events": current_events,
        "current_nodes": current_nodes,
        "current_relationships": current_relationships,
        "type_counts": type_counts,
        "cluster_activity": cluster_activity,
        "has_history": last_briefing is not None,
        "last_briefing_events": last_briefing["event_count"] if last_briefing else None,
        "last_briefing_nodes": last_briefing["node_count"] if last_briefing else None,
        "last_briefing_relationships": last_briefing["relationship_count"] if last_briefing else None,
        "last_briefing_at": last_briefing["created_at"] if last_briefing else None,
    }

    if last_briefing:
        if last_briefing.get("event_count") is not None:
            delta = current_events - last_briefing["event_count"]
            facts["event_pressure_delta"] = delta
            facts["pressure_direction"] = (
                "increased" if delta > 0 else "decreased" if delta < 0 else "steady"
            )

        last_nodes = last_briefing.get("node_count", 0)
        last_rels = last_briefing.get("relationship_count", 0)
        # Calculate deltas only if there was a previous node/relationship count logged
        facts["node_growth"] = current_nodes - last_nodes if last_nodes > 0 else 0
        facts["relationship_growth"] = current_relationships - last_rels if last_rels > 0 else 0

    return facts


# ─────────────────────────────────────────────────────────────────────────
# 4. AWARE BRIEFING — the narrative Woo speaks, referencing its own past
# ─────────────────────────────────────────────────────────────────────────

async def build_aware_briefing(driver, window_hours: int = 6, write_log: bool = True, override_message: str = None) -> dict:
    facts = await compute_continuity(driver, window_hours)
    lines = []

    # Anchor: what the Grid holds in memory
    lines.append(f"The Grid holds {facts['current_events']} events in memory.")

    # Continuity reference — compared to the last briefing
    if facts.get("has_history") and "event_pressure_delta" in facts:
        delta = facts["event_pressure_delta"]
        if delta > 0:
            lines.append(f"Compared to the last briefing, event pressure has increased by {delta}.")
        elif delta < 0:
            lines.append(f"Compared to the last briefing, event pressure has eased by {abs(delta)}.")
        else:
            lines.append("Event pressure holds steady since the last briefing.")
    elif not facts.get("has_history"):
        lines.append("This is my first briefing. I have no prior memory to compare against yet.")

    # Repeated-signal recall — "I remember a similar signal"
    repeats = [t for t in facts["type_counts"] if t["count"] > 1 and t["type"] != "unknown"]
    if repeats:
        top = repeats[0]
        lines.append(f"I remember a similar signal: {top['type']} has recurred {top['count']} times recently.")

    # Cluster awareness — stability vs repetition
    for c in facts["cluster_activity"]:
        cid = c["cluster"]
        count = c["count"]
        if cid == "unknown":
            continue
        if count > 5:
            lines.append(f"{cid} shows heightened activity — {count} observations.")
        elif count > 1:
            lines.append(f"{cid} has repeated observations.")
        else:
            lines.append(f"{cid} remains stable.")

    narrative = override_message if override_message is not None else " ".join(lines)

    # Persist this briefing so the NEXT one can compare against it
    if write_log:
        async with driver.session(database=NEO4J_DATABASE) as session:
            await session.run("""
                CREATE (b:BriefingLog {
                    id: $b_id,
                    message: $message,
                    created_at: $created_at,
                    event_count: $event_count,
                    node_count: $node_count,
                    relationship_count: $relationship_count,
                    referenced_previous: $has_history,
                    cluster_id: $cluster_id,
                    source: 'aware_briefing_builder',
                    created_by: 'build_aware_briefing',
                    source_type: 'ai_generated',
                    verification_status: 'unverified',
                    operational_trust: 'reference',
                    seal: 'Synthetic'
                })
            """, b_id=f"brief_aware_{int(datetime.now(timezone.utc).timestamp())}",
                 message=narrative,
                 created_at=_now_iso(),
                 event_count=facts["current_events"],
                 node_count=facts["current_nodes"],
                 relationship_count=facts["current_relationships"],
                 has_history=facts.get("has_history", False),
                 cluster_id=MOSTAR_CLUSTER_ID)

    return {
        "message": narrative,
        "facts": facts,
        "generated_at": _now_iso(),
        "seal": "🜃∴🜂",
    }
