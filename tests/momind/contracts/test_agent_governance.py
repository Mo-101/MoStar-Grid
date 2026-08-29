"""Governance tests for canonical AgentDeclaration, Ecosystem, and MoScript."""
from __future__ import annotations

import pytest

from entity.ecosystem import AgentDeclaration, AgentNotFound, Ecosystem, GovernanceViolation
from moscript import MoScript, MoScriptEngine
from moscript.runtime import GovernanceEngine


def _declaration(**overrides) -> AgentDeclaration:
    base = {
        "id": "mo-test-agent-001",
        "role": "Test Agent",
        "permissions": ("agent.execute",),
        "element": "shadow",
        "owner": "user-1",
        "truth_threshold": 0.0,
        "provenance": "authored",
        "attested_by": "truth-engine",
        "origin_model": "phi-4",
    }
    base.update(overrides)
    return AgentDeclaration(**base)


def test_self_attestation_raises():
    with pytest.raises(GovernanceViolation):
        _declaration(attested_by="phi-4", origin_model="phi-4")


def test_invalid_truth_threshold_raises():
    with pytest.raises(GovernanceViolation):
        _declaration(truth_threshold=1.5)


def test_missing_permissions_raises():
    with pytest.raises(GovernanceViolation):
        _declaration(permissions=())


def test_valid_declaration():
    d = _declaration()
    assert d.has_permission("agent.execute")
    assert not d.has_permission("agent.write")


def test_ecosystem_require_agent_found_and_missing():
    eco = Ecosystem.in_memory()
    eco.register(_declaration())
    assert eco.require_agent("mo-test-agent-001").id == "mo-test-agent-001"
    with pytest.raises(AgentNotFound):
        eco.require_agent("mo-missing-001")


def test_governance_missing_ecosystem():
    g = GovernanceEngine()
    dec = g.govern("mo-test-agent-001", "agent.execute", ecosystem=None)
    assert dec.decision == "DENY"
    assert "MISSING_ECOSYSTEM" in dec.reason_codes


def test_governance_unknown_agent():
    g = GovernanceEngine()
    eco = Ecosystem.in_memory()
    dec = g.govern("mo-test-agent-001", "agent.execute", ecosystem=eco)
    assert dec.decision == "DENY"
    assert "UNKNOWN_AGENT" in dec.reason_codes


def test_governance_permission_denied():
    g = GovernanceEngine()
    eco = Ecosystem.in_memory()
    eco.register(_declaration(permissions=("agent.read",)))
    dec = g.govern("mo-test-agent-001", "agent.execute", ecosystem=eco)
    assert dec.decision == "DENY"
    assert "PERMISSION_DENIED" in dec.reason_codes


def test_governance_truth_threshold_denied():
    g = GovernanceEngine()
    eco = Ecosystem.in_memory()
    eco.register(_declaration(permissions=("agent.execute",), truth_threshold=0.9))
    dec = g.govern("mo-test-agent-001", "agent.execute", ecosystem=eco, context={"truth_score": 0.5})
    assert dec.decision == "DENY"
    assert "TRUTH_THRESHOLD" in dec.reason_codes


def test_governance_allowed():
    g = GovernanceEngine()
    eco = Ecosystem.in_memory()
    eco.register(_declaration())
    dec = g.govern("mo-test-agent-001", "agent.execute", ecosystem=eco)
    assert dec.decision == "ALLOW"
    assert dec.result["agent_id"] == "mo-test-agent-001"


def test_moscript_engine_register_requires_declaration():
    engine = MoScriptEngine()
    script = MoScript(
        id="mo-rogue-001",
        name="Rogue Agent",
        trigger="on_query",
        inputs=["x"],
        logic=lambda ctx: ctx,
        voice_line="...",
        sass="...",
    )
    with pytest.raises(ValueError):
        engine.register(script)


def test_moscript_engine_builtin_allowed():
    engine = MoScriptEngine()
    results = engine.fire_trigger("on_query", {"truth_passed": True, "truth_scores": {}})
    assert results
    for r in results:
        assert r["fired"]
        assert r["decision"]["decision"] == "ALLOW"


def test_moscript_engine_custom_script_governed():
    eco = Ecosystem.in_memory()
    eco.register(_declaration(id="mo-custom-001"))
    engine = MoScriptEngine(ecosystem=eco)
    engine.register(MoScript(
        id="mo-custom-001",
        name="Custom Agent",
        trigger="on_test",
        inputs=["x"],
        logic=lambda ctx: {"ok": True},
        voice_line="...",
        sass="...",
    ))
    results = engine.fire_trigger("on_test", {})
    assert len(results) == 1
    assert results[0]["fired"]
    assert results[0]["decision"]["decision"] == "ALLOW"
