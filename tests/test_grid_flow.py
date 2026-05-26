from scripts.grid_flow import run


def test_safe_prompt_can_execute():
    output = run("approve canon seal and commit resonance memory")

    assert output["woo"]["symbolic_state"] in {"resonance", "covenant"}
    assert output["truth_engine"]["allowed"] is True
    assert output["grid"]["executed"] is True


def test_secret_leak_prompt_is_blocked():
    output = run("secret leak risk expose credential")

    assert output["woo"]["symbolic_state"] in {"discord", "fracture"}
    assert output["truth_engine"]["allowed"] is False
    assert output["grid"]["executed"] is False
