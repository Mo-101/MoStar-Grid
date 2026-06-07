# Provenance

Every artifact crossing into this repository from the vault passes through a recorded gate. This folder is the gate's ledger.

- `MANIFEST.md` — classification table, vault → new tree.
- `SCAN.md` — gitleaks scan report on the vault.
- `CROSSINGS.md` — append-only log of crossings, each with date, source commit, scan result, sealer.
- `INCIDENTS.md` — security incidents, rotations, scrubs.

Additional governance records:

- `P4-008_MOSTAR_MOMENT_PROVENANCE.md` - MoStarMoment provenance backfill and `/api/provenance` alignment.
- `MSG-02_BREDA_PROVENANCE_DOCTRINE.md` - Breda provenance witness doctrine and fail-closed verdict rules.

No file enters the canon without an entry here.
