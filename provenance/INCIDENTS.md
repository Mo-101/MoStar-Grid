# Security Incidents

Append-only. Format: date, scope, action taken, evidence.

## 2026-04 — Vault leak inventory at archive seal

Discovered during pre-migration gitleaks scan of `MoStar-Grid` (archive). 24 findings, 5 categories of real exposure:

| Item | Action |
|---|---|
| `.ollama/.ollama/id_ed25519` | Rotate. Track in this file when complete. |
| `(2).env` | Rotate all values within. |
| `seed_dashboard.bat` x4 | Rotate embedded API keys. |
| `*swagger.json` with example keys | Rotate. |
| `"Perfect, Overlord ⚡️ — this is exac.txt"` | Audit any tokens visible in transcript. Rotate. |

Status: **rotation pending — must complete before new repo goes public at Phase 3.6 landing**.
