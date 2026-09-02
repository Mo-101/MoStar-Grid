"""Execution monopoly: the moscript native binary may only be invoked through RuntimeManager."""
from __future__ import annotations

import pathlib
import subprocess


ROOT = pathlib.Path(__file__).resolve().parents[3]
CHECK_SCRIPT = (
    ROOT / "core" / "protocols" / "moscript" / "scripts" / "check_execution_monopoly.py"
)


def test_no_direct_moscript_binary_calls():
    result = subprocess.run(
        ["python3", str(CHECK_SCRIPT)],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "EXECUTION_MONOPOLY_OK" in result.stdout
