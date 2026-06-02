# Gitleaks Scan — Vault (Pre-Crossing)

**Source:** `MoStar-Grid` archive repository
**Tool:** gitleaks v8.18.4
**Commits scanned:** 41
**Findings:** 24
**Raw report:** `provenance/scan-archive.json`

## By rule

| Rule | Count |
|---|---|
| generic-api-key | 23 |
| private-key | 1 |

## Real exposures (must rotate)

| File | Commit | Disposition |
|---|---|---|
| `.ollama/.ollama/id_ed25519` | various | Rotate. Private ED25519 key. Was on public GitHub. |
| `(2).env` | top-level | Rotate every value. |
| `backend/neo4j-mostar-industries/import/data/scripts/seed_dashboard.bat` | 827f4cb2 | Rotate embedded API keys. |
| `backend/neo4j-mostar-industries/import/seed_dashboard.bat` | 827f4cb2 | Rotate. |
| `memory/neo4j-mindgraph/data/data/scripts/seed_dashboard.bat` | 827f4cb2 | Rotate. |
| `memory/neo4j-mindgraph/data_wired_default/data/scripts/seed_dashboard.bat` | 827f4cb2 | Rotate. |
| `memory/neo4j-mindgraph/import/data/scripts/seed_dashboard.bat` | 827f4cb2 | Rotate. |
| `memory/neo4j-mindgraph/import/seed_dashboard.bat` | 827f4cb2 | Rotate. |
| `*/AkanimoIniobong-mo-star_ai_api-1.0.0-swagger.json` (3 copies) | 827f4cb2 / 0c3a27b9 | Rotate any real keys; regenerate spec without examples. |
| `"Perfect, Overlord ⚡️ — this is exac.txt"` (3 copies) | various | Audit transcript; rotate any visible tokens. |

## False positives (third-party test fixtures)

| File | Reason |
|---|---|
| `.venv-wsl/lib/python3.12/site-packages/numpy/random/tests/test_generator_mt19937.py` (6 hits) | NumPy MT19937 test vectors — cryptographic test data, not secrets. |
| `.venv-wsl/lib/python3.12/site-packages/edge_tts/constants.py` | Public library constant. |

## Concentration
- 18 of 24 findings land in commit `827f4cb2` (WIP Ollama troubleshooting). That commit is the contamination crater.
