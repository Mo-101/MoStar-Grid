"""Runtime tests for `mo-mind-attestation-guard-001`."""
from __future__ import annotations

from moscript.runtime.contract_decision import ContractDecision


def test_self_attestation_becomes_candidate(engine):
    dec = engine.evaluate(
        "mo-mind-attestation-guard-001",
        {
            "candidate_claim": "x",
            "origin_model": "phi-4",
            "attested_by": "phi-4",
        },
        principal="user-1",
    )
    assert isinstance(dec, ContractDecision)
    assert dec.decision == "STAGE_CANDIDATE"
    assert "SELF_ATTESTATION" in dec.reason_codes
    assert dec.result["candidate_status"] == "candidate"
    assert dec.result["target_state"] == "non_canonical"


def test_other_attestation_becomes_candidate(engine):
    dec = engine.evaluate(
        "mo-mind-attestation-guard-001",
        {
            "candidate_claim": "x",
            "origin_model": "phi-4",
            "attested_by": "truth-engine",
        },
        principal="user-1",
    )
    assert dec.decision == "STAGE_CANDIDATE"
    assert "UNCORROBORATED" in dec.reason_codes
    assert dec.result["candidate_status"] == "candidate"
