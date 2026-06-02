"""Graph density telemetry for Phase 4.0a promotion readiness."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone

from grid.config import MOSTAR_CLUSTER_ID, NEO4J_DATABASE


@dataclass
class DensitySnapshot:
    timestamp: str
    total_nodes: int
    total_relationships: int
    meaningful_relationships: int
    provenance_chains: int
    label_distribution: dict
    avg_degree: float
    canonical_coverage: float

    def to_dict(self) -> dict:
        return asdict(self)


class DensityTelemetry:
    def __init__(self, mindgraph, canonical_coverage: float = 0.0):
        self.mindgraph = mindgraph
        self.canonical_coverage = canonical_coverage

    async def snapshot(self) -> DensitySnapshot:
        if not self.mindgraph.connected:
            return DensitySnapshot(
                timestamp=_now(),
                total_nodes=0,
                total_relationships=0,
                meaningful_relationships=0,
                provenance_chains=0,
                label_distribution={},
                avg_degree=0.0,
                canonical_coverage=self.canonical_coverage,
            )

        cypher = """
        CALL {
            MATCH (n {cluster_id: $cluster_id}) RETURN count(n) AS total_nodes
        }
        CALL {
            MATCH (a {cluster_id: $cluster_id})-[r]->(b {cluster_id: $cluster_id})
            RETURN count(r) AS total_relationships
        }
        CALL {
            MATCH (a {cluster_id: $cluster_id})-[r]->(b {cluster_id: $cluster_id})
            WHERE NOT type(r) IN ['SEALED_FROM']
            RETURN count(r) AS meaningful_relationships
        }
        CALL {
            MATCH (m:MoStarMoment {cluster_id: $cluster_id})-[:SEALED_FROM]->()
            RETURN count(m) AS provenance_chains
        }
        CALL {
            MATCH (n {cluster_id: $cluster_id})
            UNWIND labels(n) AS label
            WITH label, count(*) AS count
            RETURN collect({label: label, count: count}) AS labels
        }
        RETURN total_nodes, total_relationships, meaningful_relationships,
               provenance_chains, labels
        """
        async with self.mindgraph._driver.session(database=NEO4J_DATABASE) as session:
            result = await session.run(cypher, cluster_id=MOSTAR_CLUSTER_ID)
            record = await result.single()

        total_nodes = record["total_nodes"] if record else 0
        total_relationships = record["total_relationships"] if record else 0
        return DensitySnapshot(
            timestamp=_now(),
            total_nodes=total_nodes,
            total_relationships=total_relationships,
            meaningful_relationships=record["meaningful_relationships"] if record else 0,
            provenance_chains=record["provenance_chains"] if record else 0,
            label_distribution={item["label"]: item["count"] for item in (record["labels"] if record else [])},
            avg_degree=round(total_relationships / total_nodes, 3) if total_nodes else 0.0,
            canonical_coverage=self.canonical_coverage,
        )

    async def check_promotion_readiness(self) -> dict:
        snapshot = await self.snapshot()
        gaps = []
        if snapshot.meaningful_relationships < 10000:
            gaps.append("meaningful_relationships below 10000")
        if snapshot.provenance_chains < 500:
            gaps.append("provenance_chains below 500")
        if snapshot.canonical_coverage < 1.0:
            gaps.append("canonical ontology coverage not human-declared complete")
        gaps.append("contradiction corpus must be human-verified")
        return {"ready": False if gaps else True, "gaps": gaps}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
