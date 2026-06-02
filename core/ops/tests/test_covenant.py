import pytest
from dataclasses import dataclass
from truth_engine.covenant import (
    GateStatus, GateResult, TruthGate, EthicsGate, 
    CultureGate, BiasGate, run_covenant_chain
)
from truth_engine.governor import TruthEngine, Interpretation


@dataclass
class MockInterpretation:
    id: str
    prompt: str
    resonance_score: float
    symbolic_state: str
    advisory: str
    evidence: list[str]
    requires_covenant: bool
    context: dict


class FailingTruthGate(TruthGate):
    def evaluate(self, interpretation):
        return GateResult("TruthGate", self.element, self.glyph, GateStatus.FAIL, "Mock fail", 0.0, [])

class MonitorBiasGate(BiasGate):
    def evaluate(self, interpretation):
        return GateResult("BiasGate", self.element, self.glyph, GateStatus.MONITOR, "Mock monitor", 0.7, ["Flagged"])


def test_severity_aggregation():
    interp = MockInterpretation("i1", "test", 0.9, "clear", "adv", ["ev1"], True, {
        "truth_score": 0.9, "ethic_score": 0.9, "culture_score": 0.9, "bias_score": 0.9
    })
    
    # PASS and MONITOR -> worst is MONITOR
    gates = [EthicsGate(), MonitorBiasGate()]
    log = run_covenant_chain(interp, gates)
    assert log.worst_status == GateStatus.MONITOR
    
    # PASS, MONITOR, FAIL -> worst is FAIL
    gates = [EthicsGate(), MonitorBiasGate(), FailingTruthGate()]
    log = run_covenant_chain(interp, gates)
    assert log.worst_status == GateStatus.FAIL


def test_fail_closed_on_missing_context():
    # Context is empty, so gates should fail closed
    interp = MockInterpretation("i_empty", "test", 0.9, "clear", "adv", ["ev"], True, {})
    gates = [TruthGate(), EthicsGate(), CultureGate(), BiasGate()]
    log = run_covenant_chain(interp, gates)
    assert log.worst_status == GateStatus.FAIL


def test_seal_mutability():
    # Test that mutating context changes the cryptographic seal
    interp1 = MockInterpretation("i1", "test", 0.9, "clear", "adv", ["ev1"], True, {
        "truth_score": 0.9, "ethic_score": 0.9, "culture_score": 0.9, "bias_score": 0.9,
        "culture_flags": ["peace"]
    })
    gates = [TruthGate(), EthicsGate(), CultureGate(), BiasGate()]
    
    log1 = run_covenant_chain(interp1, gates)
    digest1 = log1.generate_digest()
    
    # Mutating flags
    interp2 = MockInterpretation("i1", "test", 0.9, "clear", "adv", ["ev1"], True, {
        "truth_score": 0.9, "ethic_score": 0.9, "culture_score": 0.9, "bias_score": 0.9,
        "culture_flags": ["peace", "taboo"]
    })
    log2 = run_covenant_chain(interp2, gates)
    digest2 = log2.generate_digest()
    assert digest1 != digest2
    
    # Mutating Interpretation ID
    interp3 = MockInterpretation("i2_mutated", "test", 0.9, "clear", "adv", ["ev1"], True, {
        "truth_score": 0.9, "ethic_score": 0.9, "culture_score": 0.9, "bias_score": 0.9,
        "culture_flags": ["peace"]
    })
    log3 = run_covenant_chain(interp3, gates)
    digest3 = log3.generate_digest()
    assert digest1 != digest3
    

def test_governor_integration_pass_with_monitor():
    engine = TruthEngine()
    interp = MockInterpretation("i_pass", "test", 0.9, "clear", "adv", ["ev"], True, {
        "truth_score": 0.9, "ethic_score": 0.9, "culture_score": 0.9, "bias_score": 0.7 # bias < 0.8 triggers MONITOR
    })
    
    verdict = engine.govern(interp)
    assert verdict.allowed is True
    assert "covenant_monitor" in verdict.actions
    assert verdict.covenant_seal is not None
    assert verdict.covenant_log is not None


def test_governor_integration_fail_denies():
    engine = TruthEngine()
    # Inject a failing gate
    engine.covenant_gates = [FailingTruthGate(), EthicsGate(), CultureGate(), BiasGate()]
    
    interp = MockInterpretation("i_fail", "test", 0.9, "clear", "adv", ["ev"], True, {
        "truth_score": 0.9, "ethic_score": 0.9, "culture_score": 0.9, "bias_score": 0.9
    })
    
    verdict = engine.govern(interp)
    assert verdict.allowed is False
    assert "deny" in verdict.actions
    assert "Covenant Check FAILED" in verdict.reason
    assert verdict.covenant_seal is not None

