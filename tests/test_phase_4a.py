import asyncio

import pytest

from approval_queue import ApprovalQueue, ProposalRecord, ProposalState
from grid.orchestrator import CommitForbiddenError, GridOrchestrator
from mindgraph import CommitForbiddenError as MindGraphCommitForbiddenError
from mindgraph import MindGraph


def test_learn_without_commit_token_raises():
    graph = MindGraph()

    with pytest.raises(MindGraphCommitForbiddenError):
        asyncio.run(graph.learn(category="canon", content="sealed canon"))


def test_stamp_moment_without_commit_token_raises():
    graph = MindGraph()

    with pytest.raises(MindGraphCommitForbiddenError):
        asyncio.run(graph.stamp_moment("talk", "think", "mem_1"))


def test_commit_with_expired_token_raises():
    graph = MindGraph()
    token = graph.begin_commit()
    graph.end_commit(token)

    with pytest.raises(MindGraphCommitForbiddenError):
        asyncio.run(graph.learn(category="canon", content="sealed canon", _commit_token=token))


def test_queue_survives_restart(tmp_path):
    queue_path = tmp_path / "proposals.jsonl"
    queue = ApprovalQueue(queue_path)
    proposal = ProposalRecord(
        id="proposal_test",
        state=ProposalState.PROPOSED,
        canon_input="MoStar canon survives restart.",
        interpretation={},
        consistency={},
        placement={},
        proposed_mutations=[],
        proposed_at="2026-05-26T00:00:00+00:00",
    )

    asyncio.run(queue.enqueue(proposal))
    reloaded = ApprovalQueue(queue_path)

    assert asyncio.run(reloaded.get("proposal_test")).canon_input == proposal.canon_input


def test_commit_on_proposed_state_raises(tmp_path):
    orchestrator = GridOrchestrator()
    orchestrator.approval_queue = ApprovalQueue(tmp_path / "proposals.jsonl")
    proposal = ProposalRecord(
        id="proposal_unapproved",
        state=ProposalState.PROPOSED,
        canon_input="Unapproved canon cannot commit.",
        interpretation={"category": "canon"},
        consistency={},
        placement={},
        proposed_mutations=[],
        proposed_at="2026-05-26T00:00:00+00:00",
    )
    asyncio.run(orchestrator.approval_queue.enqueue(proposal))

    with pytest.raises(CommitForbiddenError):
        asyncio.run(orchestrator.commit_after_seal("proposal_unapproved"))
