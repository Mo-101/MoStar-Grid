import asyncio
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from neo4j import GraphDatabase

from approval_queue import ApprovalQueue, ProposalRecord, ProposalState
from grid.api import app
from grid.config import (
    APPROVAL_QUEUE_PATH,
    MOSTAR_CLUSTER_ID,
    MOSTAR_CLUSTER_NAME,
    NEO4J_URI,
    NEO4J_USER,
    PROVENANCE_PATH,
    ensure_cluster_dirs,
    # The password is no longer a module constant — it is released from the
    # attested vault (back/services/grid/credentials.py). Importing the old
    # NEO4J_PASSWORD name made this whole module fail at collection.
    get_neo4j_password,
)
from grid.orchestrator import CommitResult, GridOrchestrator


def test_cluster_directory_structure_created():
    ensure_cluster_dirs()

    assert APPROVAL_QUEUE_PATH.parent.exists()
    assert PROVENANCE_PATH.parent.exists()
    assert f"clusters/{MOSTAR_CLUSTER_ID}/approval_queue" in APPROVAL_QUEUE_PATH.as_posix()
    assert f"clusters/{MOSTAR_CLUSTER_ID}/provenance" in PROVENANCE_PATH.as_posix()


def test_api_status_includes_cluster_metadata():
    client = TestClient(app)

    response = client.get("/api/status")

    assert response.status_code == 200
    payload = response.json()
    assert payload["cluster_id"] == MOSTAR_CLUSTER_ID
    assert payload["cluster_name"] == MOSTAR_CLUSTER_NAME


def test_all_proposals_carry_cluster_id(tmp_path):
    orchestrator = GridOrchestrator()
    orchestrator.approval_queue = ApprovalQueue(tmp_path / "proposals.jsonl")

    proposal = asyncio.run(orchestrator.propose("Cluster-local proposal identity test."))

    assert proposal.cluster_id == MOSTAR_CLUSTER_ID
    assert proposal.to_dict()["cluster_id"] == MOSTAR_CLUSTER_ID


def test_all_scrolls_carry_cluster_id():
    scroll = CommitResult(
        proposal_id="proposal_test",
        cluster_id=MOSTAR_CLUSTER_ID,
        state=ProposalState.COMMITTED.value,
        memory_id="mem_test",
        moment_id="moment_test",
        committed_at="2026-05-27T00:00:00+00:00",
        seal="seal",
    )

    assert scroll.to_dict()["cluster_id"] == MOSTAR_CLUSTER_ID


def test_multiple_sequential_clusters_can_coexist_on_same_machine(tmp_path):
    alpha_path = tmp_path / "clusters" / "nairobi-alpha" / "approval_queue" / "proposals.jsonl"
    beta_path = tmp_path / "clusters" / "kampala-beta" / "approval_queue" / "proposals.jsonl"
    alpha = ApprovalQueue(alpha_path)
    beta = ApprovalQueue(beta_path)

    asyncio.run(alpha.enqueue(_proposal("proposal_alpha", "nairobi-alpha")))
    asyncio.run(beta.enqueue(_proposal("proposal_beta", "kampala-beta")))

    assert asyncio.run(alpha.get("proposal_alpha")).cluster_id == "nairobi-alpha"
    assert asyncio.run(beta.get("proposal_beta")).cluster_id == "kampala-beta"
    assert alpha_path.exists()
    assert beta_path.exists()


def test_neo4j_nodes_include_cluster_id_property():
    try:
        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, get_neo4j_password()))
        driver.verify_connectivity()
    except Exception as exc:
        pytest.skip(f"Neo4j unavailable for cluster identity check: {exc}")

    try:
        with driver.session() as session:
            missing = session.run(
                """
                MATCH (n)
                WHERE n.cluster_id IS NULL
                RETURN count(n) AS missing
                """
            ).single()["missing"]
    finally:
        driver.close()

    assert missing == 0


def test_neo4j_foundation_nodes_are_sealed_grid_components():
    try:
        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, get_neo4j_password()))
        driver.verify_connectivity()
    except Exception as exc:
        pytest.skip(f"Neo4j unavailable for foundation seal check: {exc}")

    try:
        with driver.session() as session:
            record = session.run(
                """
                MATCH (n {cluster_id: $cluster_id})
                RETURN
                    count(n) AS total,
                    sum(CASE WHEN n:GridComponent THEN 1 ELSE 0 END) AS grid_components,
                    sum(CASE WHEN n.sealed = true THEN 1 ELSE 0 END) AS sealed,
                    sum(CASE WHEN n.mostar_moment_seal IS NOT NULL THEN 1 ELSE 0 END) AS moment_sealed,
                    sum(CASE WHEN n:Agent AND n.sacred = true THEN 1 ELSE 0 END) AS sacred_agents,
                    sum(CASE WHEN NOT (n)--() THEN 1 ELSE 0 END) AS orphaned
                """,
                cluster_id=MOSTAR_CLUSTER_ID,
            ).single()
    finally:
        driver.close()

    assert record["total"] == 18
    assert record["grid_components"] == 18
    assert record["sealed"] == 18
    assert record["moment_sealed"] == 18
    assert record["sacred_agents"] == 4
    assert record["orphaned"] == 0


def _proposal(proposal_id: str, cluster_id: str) -> ProposalRecord:
    return ProposalRecord(
        id=proposal_id,
        state=ProposalState.PROPOSED,
        canon_input=f"{cluster_id} local proposal",
        interpretation={},
        consistency={},
        placement={},
        proposed_mutations=[],
        proposed_at="2026-05-27T00:00:00+00:00",
        cluster_id=cluster_id,
    )
