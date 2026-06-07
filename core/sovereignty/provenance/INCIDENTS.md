# Security Incidents

Append-only. Format: date, scope, action taken, evidence.

## 2026-06-07 - GitHub push rejected by Neo4j runtime transaction files

Scope: GitHub rejected an attempted push because unpushed local history contained Neo4j runtime transaction files over 100 MiB.

Action required:

```text
no push occurred
rewrite local unpushed history to remove runtime DB artifacts
update `.gitignore` to prevent future Neo4j data commits
keep Neo4j runtime graph state in Neo4j/backups, not Git history
```

Status: **cleanup in progress**.

## 2026-06-07 - Neo4j local credential exposure in working-session command

Scope: local Neo4j development credential was exposed in a working-session command/context.

Action required:

```text
rotate Neo4j password before any shared commit/log/export
update local `.env` only
restart dependent PM2 services after rotation
do not paste the rotated value into chat, commit messages, logs, or docs
```

Status: **rotation pending**.

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
