from __future__ import annotations

import asyncio
import sys
from pathlib import Path


SERVICES = Path(__file__).resolve().parents[3] / "back" / "services"
if str(SERVICES) not in sys.path:
    sys.path.insert(0, str(SERVICES))

from mindgraph import MindGraph  # noqa: E402


class _Result:
    async def single(self):
        return {
            "nodes": 125_000,
            "relationships": 420_000,
            "labels": ["Metric", "RuntimeEvent"],
            "cluster_nodes": 25_316,
            "cluster_relationships": 95,
            "cluster_labels": ["RuntimeEvent"],
        }


class _Session:
    def __init__(self):
        self.cypher = ""
        self.parameters = {}

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_args):
        return None

    async def run(self, cypher, **parameters):
        self.cypher = cypher
        self.parameters = parameters
        return _Result()


class _Driver:
    def __init__(self):
        self.last_session = None

    def session(self, **_kwargs):
        self.last_session = _Session()
        return self.last_session


def test_graph_stats_expose_database_census_and_cluster_subset():
    graph = MindGraph()
    graph._driver = _Driver()

    stats = asyncio.run(graph.get_graph_stats())

    assert stats["scope"] == "database"
    assert stats["nodes"] == 125_000
    assert stats["relationships"] == 420_000
    assert stats["cluster"]["nodes"] == 25_316
    assert stats["cluster"]["relationships"] == 95
    assert "MATCH (n) RETURN count(n) AS nodes" in graph._driver.last_session.cypher
    assert "MATCH ()-[r]->() RETURN count(r) AS relationships" in graph._driver.last_session.cypher
