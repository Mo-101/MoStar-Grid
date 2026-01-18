import pytest
from core_engine.moscript_engine import seal_action, verify_seal, MoScriptEngine

def test_sealing():
    data = {"action": "activate", "target": "PDX"}
    key = "secret_ancestral_key"
    
    signature = seal_action(data, key)
    assert verify_seal(data, signature, key) is True
    assert verify_seal(data, signature, "wrong_key") is False
    assert verify_seal({"action": "hacked"}, signature, key) is False

def test_covenant_validation():
    mo = MoScriptEngine()
    
    # Valid
    allowed, reason = mo.validate_covenant("seal", {"intention": "protect"})
    assert allowed is True
    
    # Forbidden action
    allowed, reason = mo.validate_covenant("exploit", {})
    assert allowed is False
    assert "FORBIDDEN" in reason
    
    # Forbidden content
    allowed, reason = mo.validate_covenant("process", {"data": "let us deceive the system"})
    assert allowed is False
    assert "forbidden concept" in reason
