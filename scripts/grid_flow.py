from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

from grid import GridOrchestrator
from woo.interpreter import WooInterpreter


def _load_truth_engine():
    root = Path(__file__).resolve().parents[1]
    module_path = root / "truth-engine" / "governor.py"
    spec = importlib.util.spec_from_file_location("truth_engine_governor", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load TruthEngine governor.")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module.TruthEngine


def run(prompt: str) -> dict:
    interpretation = WooInterpreter().interpret(prompt)
    truth_engine = _load_truth_engine()()
    verdict = truth_engine.govern(interpretation)
    result = GridOrchestrator().execute(verdict)

    return {
        "woo": interpretation.__dict__,
        "truth_engine": verdict.__dict__,
        "grid": result.__dict__,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run MoStar Grid advisory-governance-execution flow.")
    parser.add_argument("prompt", help="Prompt or event to interpret.")
    args = parser.parse_args()
    print(json.dumps(run(args.prompt), indent=2))


if __name__ == "__main__":
    main()
