import asyncio
from types import SimpleNamespace

import pytest

from approval_queue import ApprovalQueue
from control_plane_runtime import (
    MemoryEnforcementStateProvider,
    RuntimeEnforcementDenied,
    RuntimeEnforcementGate,
)
from grid.orchestrator import CommitForbiddenError, GridOrchestrator
from moscript import MoScript, MoScriptEngine


def gate(levels):
    provider = MemoryEnforcementStateProvider(levels)
    return RuntimeEnforcementGate(provider=provider, enabled=True), provider


def test_info_allows_and_audits_all_four_surfaces():
    runtime_gate, provider = gate({})
    contexts = {
        "agents": {"operation_class": "conversation"},
        "mo_woo_nexus": {"side_effecting": False},
        "decision_engine": {},
        "moscript_registry": {"runtime_id": "mo-grid-heartbeat-001"},
    }
    for surface, context in contexts.items():
        assert runtime_gate.require(surface, "test", context).allowed
    assert len(provider.decisions) == 4
    assert all(decision.level == "INFO" for decision in provider.decisions)


@pytest.mark.parametrize("surface,component", [
    ("agents", "agents"),
    ("mo_woo_nexus", "mo_woo_nexus"),
    ("decision_engine", "decision_engine"),
    ("moscript_registry", "moscript_registry"),
])
def test_locked_blocks_and_audits_every_surface(surface, component):
    runtime_gate, provider = gate({component: "LOCKED"})
    with pytest.raises(RuntimeEnforcementDenied):
        runtime_gate.require(surface, "test", {"runtime_id": "mo-grid-heartbeat-001"})
    assert provider.decisions[-1].allowed is False
    assert provider.decisions[-1].level == "LOCKED"


def test_restricted_surface_rules_are_distinct():
    runtime_gate, _ = gate({
        "agents": "RESTRICTED",
        "mo_woo_nexus": "RESTRICTED",
        "decision_engine": "RESTRICTED",
        "moscript_registry": "RESTRICTED",
    })
    with pytest.raises(RuntimeEnforcementDenied):
        runtime_gate.require("agents", "dcx.think", {"operation_class": "conversation"})
    assert runtime_gate.require("mo_woo_nexus", "judge", {"side_effecting": False}).allowed
    with pytest.raises(RuntimeEnforcementDenied):
        runtime_gate.require("mo_woo_nexus", "mutate", {"side_effecting": True})
    with pytest.raises(RuntimeEnforcementDenied):
        runtime_gate.require("decision_engine", "rank", {})
    assert runtime_gate.require(
        "decision_engine", "rank", {"approved": True, "secondary_auth": True}
    ).allowed
    with pytest.raises(RuntimeEnforcementDenied):
        runtime_gate.require(
            "moscript_registry", "fire", {"runtime_id": "mo-grid-heartbeat-001"}
        )
    assert runtime_gate.require(
        "moscript_registry", "fire",
        {"runtime_id": "mo-grid-heartbeat-001", "approved": True},
    ).allowed


def test_moscript_hook_runs_before_script_logic():
    calls = []

    def deny(*_):
        raise RuntimeError("blocked before fire")

    engine = MoScriptEngine(enforcement_hook=deny)
    engine.register(MoScript("test", "Test", "on_test", [], lambda _: calls.append(True), "", ""))
    with pytest.raises(RuntimeError, match="blocked before fire"):
        engine.fire_trigger("on_test", {})
    assert calls == []


def test_orchestrator_agents_gate_precedes_dcx_call():
    runtime_gate, _ = gate({"agents": "LOCKED"})
    orchestrator = GridOrchestrator(control_plane=runtime_gate)
    calls = []

    async def forbidden_dcx(**_):
        calls.append(True)

    orchestrator.dcx.think = forbidden_dcx
    with pytest.raises(CommitForbiddenError, match="agents/dcx.think denied"):
        asyncio.run(orchestrator.think("hello"))
    assert calls == []


def test_orchestrator_woo_and_decision_interception_points():
    woo_gate, _ = gate({"mo_woo_nexus": "LOCKED"})
    woo_orchestrator = GridOrchestrator(control_plane=woo_gate)
    with pytest.raises(CommitForbiddenError, match="mo_woo_nexus/woo.interpret.canon denied"):
        asyncio.run(woo_orchestrator.interpret("Canon proposal"))

    decision_gate, _ = gate({"decision_engine": "LOCKED"})
    decision_orchestrator = GridOrchestrator(control_plane=decision_gate)

    async def consistency(**_):
        return SimpleNamespace(passed=True, scores={"x": 1.0}, thresholds={}, failures=[], seal="")

    decision_orchestrator.truth.validate_consistency = consistency
    with pytest.raises(CommitForbiddenError, match="decision_engine/rank_placement denied"):
        asyncio.run(decision_orchestrator.interpret("Canon proposal"))


def test_orchestrator_moscript_interception_precedes_logic():
    runtime_gate, _ = gate({"moscript_registry": "LOCKED"})
    orchestrator = GridOrchestrator(control_plane=runtime_gate)
    with pytest.raises(CommitForbiddenError, match="moscript_registry/on_startup denied"):
        orchestrator.moscript.fire_trigger("on_startup", {})


def test_state_store_failure_is_fail_closed():
    class BrokenProvider:
        def get_level(self, _):
            raise ConnectionError("offline")

        def audit(self, _):
            raise AssertionError("unreachable")

    runtime_gate = RuntimeEnforcementGate(provider=BrokenProvider(), enabled=True)
    with pytest.raises(RuntimeEnforcementDenied) as captured:
        runtime_gate.require("agents", "dcx.think")
    assert captured.value.decision.level == "UNKNOWN"
    assert "state unavailable" in captured.value.decision.reason


def test_orchestrator_propose_reaches_truth_and_queue(tmp_path):
    """End-to-end warm-up: /api/propose → interpret → validate_consistency → queue."""
    runtime_gate, _ = gate({})
    orchestrator = GridOrchestrator(control_plane=runtime_gate)
    queue_path = tmp_path / "proposals.jsonl"
    orchestrator.approval_queue = ApprovalQueue(queue_path)
    orchestrator.provenance.record_event = lambda *_, **__: None

    # The canonical path through Woo and DecisionEngine is not the subject
    # of this test; we replace them with synthetic but shape-correct objects
    # so the test proves the routing and queue wiring, not the model layer.
    class FakeWoo:
        async def interpret(self, canon_input, graph_context, user_id="grid", source="canon"):
            return SimpleNamespace(
                category="canon",
                reasoning="synthetic grounded reasoning",
                to_dict=lambda: {"category": "canon", "reasoning": "synthetic grounded reasoning"},
            )

    class FakeDecisionEngine:
        async def rank_placement(self, interpretation, existing_context, consistency_report):
            option = SimpleNamespace(
                properties={"category": "canon"},
                labels=["Memory", "GridKnowledge"],
            )
            return SimpleNamespace(
                options=[option],
                selected=0,
                to_dict=lambda: {"selected": 0, "options": [{"category": "canon"}]},
            )

    orchestrator.woo_interpreter = FakeWoo()
    orchestrator.decision_engine = FakeDecisionEngine()

    proposal = asyncio.run(orchestrator.propose("First warm-up canon proposal"))

    # It reached validate_consistency and kept a structured result.
    assert proposal.consistency is not None
    assert "passed" in proposal.consistency
    assert "scores" in proposal.consistency
    assert "seal" in proposal.consistency

    # The result landed in the approval queue file.
    assert queue_path.exists()
    reloaded = ApprovalQueue(queue_path)
    loaded = asyncio.run(reloaded.get(proposal.id))
    assert loaded is not None
    assert loaded.canon_input == "First warm-up canon proposal"
