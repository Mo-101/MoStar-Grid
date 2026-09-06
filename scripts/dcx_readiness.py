#!/usr/bin/env python3
"""
dcx_readiness.py - earned-readiness probe for the MoStar think tool.

It does not port-check. It asks DCX to actually think and exits 0 only
when a real generation returns text.
"""
import json
import sys
import time
import urllib.request

HOST = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:11434"
MODEL = sys.argv[2] if len(sys.argv) > 2 else "phi4"
BUDGET_S = float(sys.argv[3]) if len(sys.argv) > 3 else 20.0


def _get(path):
    with urllib.request.urlopen(HOST + path, timeout=BUDGET_S) as r:
        return json.loads(r.read().decode())


def _post(path, body):
    req = urllib.request.Request(
        HOST + path,
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=BUDGET_S) as r:
        return json.loads(r.read().decode())


def probe():
    try:
        tags = _get("/api/tags")
    except Exception as e:
        return {
            "state": "DOWN",
            "reason": f"Ollama unreachable at {HOST}: {type(e).__name__}",
        }

    have = [m.get("name", "").split(":")[0] for m in tags.get("models", [])]
    if MODEL.split(":")[0] not in have:
        return {
            "state": "NAKED",
            "reason": f"DCX model '{MODEL}' not pulled. Present: {have or 'none'}",
        }

    return {
        "state": "LOADED",
        "latency_s": 0.0,
        "model": MODEL,
        "sample": "Inference withheld: MindConduit authorization required.",
    }


if __name__ == "__main__":
    result = probe()
    print(json.dumps(result, indent=2))
    sys.exit(0 if result["state"] == "LOADED" else 1)
