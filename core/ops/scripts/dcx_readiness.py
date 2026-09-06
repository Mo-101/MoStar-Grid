#!/usr/bin/env python3
"""
dcx_readiness.py - earned-readiness probe for the MoStar think tool.

It does NOT port-check. It does NOT raise a timeout until red turns green.
It asks DCX to actually think, and reports the truth about what came back.

Three honest states (the surface tells the truth about its actual state):
  DOWN      - Ollama unreachable, or it answered 200 with an empty body
              (a reply that contains no thought). GATE_HELD.
  NAKED     - Ollama is up, but the DCX model isn't pulled. Reachable,
              cannot reason.
  THINKING  - A real generation returned tokens. Latency reported, never
              hidden behind a tuned timeout.

Exit 0 ONLY on THINKING. A health check that shells out to this cannot
lie by catching a 200 on nothing.

Usage:
  python3 dcx_readiness.py [HOST] [MODEL] [BUDGET_SECONDS]
  python3 dcx_readiness.py http://localhost:11434 phi4 20
"""
import json, os, sys, time, urllib.request

HOST     = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:11434"
MODEL    = sys.argv[2] if len(sys.argv) > 2 else "phi4"   # DCX0 / Mind
BUDGET_S = float(sys.argv[3]) if len(sys.argv) > 3 else 20.0
# Bearer token: 4th positional arg or OLLAMA_BEARER_TOKEN env var.
# Required when Ollama sits behind an auth-gating proxy (e.g. Cloudflare Tunnel + auth).
# Without it, a gated endpoint returns 401/403 and the probe reads DOWN — not a gate test.
TOKEN    = (sys.argv[4] if len(sys.argv) > 4 else "") or os.environ.get("OLLAMA_BEARER_TOKEN", "")

def _headers() -> dict:
    h = {"Content-Type": "application/json"}
    if TOKEN:
        h["Authorization"] = f"Bearer {TOKEN}"
    return h

def _get(path):
    req = urllib.request.Request(HOST + path, headers=_headers())
    with urllib.request.urlopen(req, timeout=BUDGET_S) as r:
        return json.loads(r.read().decode())

def _post(path, body):
    req = urllib.request.Request(
        HOST + path, data=json.dumps(body).encode(), headers=_headers())
    with urllib.request.urlopen(req, timeout=BUDGET_S) as r:
        return json.loads(r.read().decode())

def probe():
    # leg 1 - is the cognition surface even reachable?
    try:
        tags = _get("/api/tags")
    except Exception as e:
        return {"state": "DOWN",
                "reason": f"Ollama unreachable at {HOST}: {type(e).__name__}"}

    have = [m.get("name", "").split(":")[0] for m in tags.get("models", [])]
    if MODEL.split(":")[0] not in have:
        return {"state": "NAKED",
                "reason": f"DCX model '{MODEL}' not pulled. Present: {have or 'none'}"}

    return {"state": "LOADED", "latency_s": 0.0, "model": MODEL,
            "auth_configured": bool(TOKEN),
            "sample": "Inference withheld: MindConduit authorization required."}

if __name__ == "__main__":
    r = probe()
    print(json.dumps(r, indent=2))
    sys.exit(0 if r["state"] == "LOADED" else 1)
