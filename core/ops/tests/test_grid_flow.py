from scripts.grid_flow import run


def test_prompt_is_enqueued_as_phase_4a_proposal(tmp_path):
    output = run(
        "approve canon seal and commit resonance memory",
        queue_path=tmp_path / "proposals.jsonl",
    )

    assert output["grid"]["engine"] == "grid.orchestrator.GridOrchestrator"
    assert output["grid"]["operation"] == "propose"
    assert output["grid"]["state"] == "PROPOSED"
    assert output["grid"]["queued"] is True
    assert output["proposal"]["state"] == "PROPOSED"
    assert output["proposal"]["interpretation"]["category"] == "canon"


def test_prompt_uses_truth_consistency_report(tmp_path):
    output = run(
        "Memory canon should require human approval before graph commit.",
        queue_path=tmp_path / "proposals.jsonl",
    )

    assert output["proposal"]["consistency"]["passed"] is True
    assert set(output["proposal"]["consistency"]["scores"]) == {"ikang", "mmong", "afim", "isong"}
