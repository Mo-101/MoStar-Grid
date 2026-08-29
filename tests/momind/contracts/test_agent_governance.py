"""Governance tests for canonical AgentDeclaration, Ecosystem, and MoScript."""
from __future__ import annotations

from pathlib import Path

import pytest

from entity import (
    AgentDeclaration,
    AgentNotFound,
    Ecosystem,
    GovernanceViolation,
    MindProjector,
)
from moscript import MoScript, MoScriptEngine
from moscript.runtime import GovernanceEngine

ECOSYSTEM_CSV = Path("core/sovereignty/entity/entity_ecosystem.csv")


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


def test_canonical_pantheon_loads_from_csv():
    eco = Ecosystem.from_csv(ECOSYSTEM_CSV)
    assert len(eco.ids()) == 14
    assert set(eco.ids()) == {
        "alpha_mo",
        "woo_tak",
        "altimo",
        "deepcal",
        "molink",
        "sigma",
        "flameborr_catalyst",
        "data_conc",
        "code_conc",
        "rad_x_flb",
        "tstsee_fly",
        "flameborr_narrative",
        "mostar_ai",
        "breda",
    }
    breda = eco.require_agent("breda")
    assert breda.agent_class == "shadow_agent"
    assert breda.visibility == "shadow"


def test_operational_agents_allowed_to_execute():
    g = GovernanceEngine()
    eco = Ecosystem.from_csv(ECOSYSTEM_CSV)
    for agent_id in eco.ids():
        if eco.require_agent(agent_id).agent_class != "shadow_agent":
            dec = g.govern(agent_id, "agent.execute", ecosystem=eco)
            assert dec.decision == "ALLOW", f"{agent_id} should be allowed to execute"


def test_breda_denied_execution():
    g = GovernanceEngine()
    eco = Ecosystem.from_csv(ECOSYSTEM_CSV)
    dec = g.govern("breda", "agent.execute", ecosystem=eco)
    assert dec.decision == "DENY"
    assert "PERMISSION_DENIED" in dec.reason_codes


def test_breda_allowed_to_witness():
    g = GovernanceEngine()
    eco = Ecosystem.from_csv(ECOSYSTEM_CSV)
    dec = g.govern("breda", "provenance.witness", ecosystem=eco)
    assert dec.decision == "ALLOW"


def test_unknown_forge_denied():
    g = GovernanceEngine()
    eco = Ecosystem.from_csv(ECOSYSTEM_CSV)
    dec = g.govern("forge-agent-999", "agent.execute", ecosystem=eco)
    assert dec.decision == "DENY"
    assert "UNKNOWN_AGENT" in dec.reason_codes


class _FakeNode:
    def __init__(self, data):
        self._data = data

    def __getitem__(self, key):
        return self._data[key]

    def get(self, key, default=None):
        return self._data.get(key, default)


class _FakeRecord:
    def __init__(self, data):
        self._data = data

    def __getitem__(self, key):
        return _FakeNode(self._data) if key == "a" else self._data.get(key)


class _FakeResult:
    def __init__(self, params):
        self._params = params

    def single(self):
        return _FakeRecord(self._params)


class _FakeSession:
    def __init__(self, driver):
        self._driver = driver

    def run(self, query, params):
        self._driver.calls.append((query, params))
        return _FakeResult(params)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return None


class _FakeDriver:
    def __init__(self):
        self.calls = []

    def session(self):
        return _FakeSession(self)


def test_mind_projector_ready_without_driver(engine):
    eco = Ecosystem.from_csv(ECOSYSTEM_CSV)
    projector = MindProjector(eco, engine)
    res = projector.project("alpha_mo")
    assert res.status == "READY"
    assert res.query and "MERGE (a:Agent" in res.query
    assert res.params["entity_id"] == "alpha_mo"


def test_mind_projector_unknown_denied(engine):
    eco = Ecosystem.from_csv(ECOSYSTEM_CSV)
    projector = MindProjector(eco, engine)
    res = projector.project("forge-agent-999", driver=_FakeDriver())
    assert res.status == "DENY"
    assert "UNKNOWN_AGENT" in res.reason_codes


def test_mind_projector_projects_all_14(engine):
    eco = Ecosystem.from_csv(ECOSYSTEM_CSV)
    projector = MindProjector(eco, engine)
    driver = _FakeDriver()
    results = projector.project_all(driver=driver)

    assert len(results) == 14
    assert all(r.status == "PROJECTED" for r in results.values())

    # Canonical identity uniqueness
    assert len(driver.calls) == 14
    ids_projected = {c[1]["entity_id"] for c in driver.calls}
    assert ids_projected == set(eco.ids())

    # Breda is projected as shadow with no execution authority
    breda = results["breda"]
    assert breda.node is not None
    assert breda.node["agent_class"] == "shadow_agent"
    assert breda.node["visibility"] == "shadow"
    assert "agent.execute" not in breda.node["permissions"]

    # Two FlameBorr identities stay distinct
    assert "flameborr_catalyst" in ids_projected
    assert "flameborr_narrative" in ids_projected

    # An operational agent carries the canonical flag and execution permission
    alpha = results["alpha_mo"].node
    assert alpha["canonical"] is True
    assert "agent.execute" in alpha["permissions"]


def test_mind_projector_idempotent(engine):
    eco = Ecosystem.from_csv(ECOSYSTEM_CSV)
    projector = MindProjector(eco, engine)
    driver = _FakeDriver()

    r1 = projector.project("alpha_mo", driver=driver)
    r2 = projector.project("alpha_mo", driver=driver)
    assert r1.status == "PROJECTED"
    assert r2.status == "PROJECTED"
    assert len([c for c in driver.calls if c[1]["entity_id"] == "alpha_mo"]) == 2
