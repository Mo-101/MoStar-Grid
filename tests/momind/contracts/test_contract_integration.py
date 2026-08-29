"""Cross-contract integration: memory -> filter -> model -> claim -> stage."""
from __future__ import annotations


def test_end_to_end_no_canonical_truth_mutation(engine):
    # 1. retrieve memory -> provenance filter
    memory = {
        "id": "m1",
        "license_status": "permitted",
        "consent_status": "granted",
        "withdrawn": False,
        "derivation_permitted": True,
    }
    p = engine.evaluate(
        "mo-mind-provenance-filter-001",
        memory,
        principal="user-1",
    )
    assert p.decision == "ALLOW"

    # 2. model invocation -> conduit
    c = engine.evaluate(
        "mo-mind-conduit-001",
        {
            "caller": "user-1",
            "model_runtime": "phi-4",
            "binding": {"id": "b1", "sealed": True},
            "authority": {"approved": True},
        },
        principal="user-1",
    )
    assert c.decision == "ALLOW"

    # 3. model self-claim -> attestation guard
    a = engine.evaluate(
        "mo-mind-attestation-guard-001",
        {
            "candidate_claim": "x",
            "origin_model": "phi-4",
            "attested_by": "phi-4",
        },
        principal="user-1",
    )
    assert a.decision == "STAGE_CANDIDATE"
    assert a.result["candidate_status"] == "candidate"
    assert a.result["target_state"] == "non_canonical"
