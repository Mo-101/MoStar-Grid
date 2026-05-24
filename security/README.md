# security/

- `policies/SECRETS.md` — secrets policy. Mandatory reading.
- `hooks/pre-commit` — gate hook. Install on clone:
  ```bash
  ln -sf ../../security/hooks/pre-commit .git/hooks/pre-commit
  chmod +x .git/hooks/pre-commit
  ```
- Periodic scans: run `gitleaks detect` weekly. Findings go to `provenance/INCIDENTS.md`.
