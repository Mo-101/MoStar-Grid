# Secrets Policy

## Rule
Never commit credentials, tokens, keys, or any value sourced from a `.env`. The pre-commit hook will reject them. Bypassing the hook is a canon violation.

## What lives where
- **`.env.example`** — committed. Variable names and inert defaults only.
- **`.env`** — local only, gitignored, never tracked.
- **Secrets at rest** — outside the repo. Use the operator's vault of choice (1Password, Bitwarden, age-encrypted file under `~/.mostar/secrets/`).
- **Secrets in CI** — environment variables injected at runtime by the deploy platform. Never echoed into logs.

## If a secret is exposed
1. **Rotate immediately.** A key in git history is compromised the moment it lands, even before push.
2. **Force-rotate dependents.** Anything that authenticated with the leaked value must be re-credentialed.
3. **Log the incident.** Append to `provenance/INCIDENTS.md` with date, scope, rotation evidence.
4. **Scrub history if pre-push.** If the leaked commit has not been pushed: `git reset --soft HEAD~1` and recommit clean. If pushed: rotate is the only remedy; history scrub is theatre.

## Compromised values inherited from the vault repo
The archive repository (`MoStar-Grid-Archive`) contains the following compromised material in its history. All values were rotated on the date this file was sealed:
- `.ollama/.ollama/id_ed25519` — ED25519 private key
- `(2).env` — top-level duplicate environment file
- `seed_dashboard.bat` (4 copies) — embedded API keys
- `*swagger.json` with embedded example keys
- `Perfect, Overlord ⚡️ — this is exac.txt` — chat transcript with inline secrets

See `provenance/SCAN.md` for the full gitleaks report.
