# Vault → New Tree Classification Manifest

## Decisions log

| Date | Decision | Sealed by |
|---|---|---|
| 2026-04 | New repo named `mostar-grid-core`. Old repo becomes `MoStar-Grid-Archive`, read-only. | The Flame Architect |
| 2026-04 | Ibibio corpus source of truth lives in `mostar-grid-core/soul/ibibio/`. Idim Ikang imports. | The Flame Architect |
| 2026-04 | Prime law clarified in canon: **Woo interprets, TruthEngine governs, Grid executes.** | The Flame Architect |
| 2026-05-26 | **Phase 4.0a doctrinal pivot:** first live cognition loop is **Assisted Canon Ingestion**, not governance. Governance (4.0b) waits for graph density thresholds. Epistemic structuring precedes decision. Sealed by RFC `rfcs/2026-05-phase-4.0a-canon-ingestion.md` and diagram `architecture/phase-4.0a-ingestion-loop.md`. Convergence partner: Claude. v2 governance-first runtime is **superseded** until reshape spec lands. | The Flame Architect |
| 2026-05-26 | **Human Correction Law sealed:** If human correction contradicts model interpretation, the correction is authoritative canon. Model output preserved as prior in provenance, never as truth. | The Flame Architect |
| 2026-05-26 | **Forbidden behaviors during 4.0a sealed:** autonomous graph mutation, schema mutation, automatic ontology expansion, self-generated provenance, self-modifying prompts, self-authorized execution. Any path enabling any of these fails closed. | The Flame Architect |
| 2026-05-26 | **Density promotion thresholds sealed:** ≥10k meaningful relationships, ≥500 provenance chains, contradiction corpus present, canonical ontology coverage. Threshold satisfaction does not auto-promote; promotion requires separate RFC and Flame Architect seal. | The Flame Architect |
| 2026-06-07 | **P4-008 MoStarMoment provenance gap recorded:** write schema supports provenance fields, but live graph inspection found most existing `MoStarMoment` nodes untagged. Backfill must be conservative and preserve existing nodes. | Codex |
| 2026-06-07 | **MSG-02 Breda provenance doctrine recorded:** Breda witnesses provenance and fails closed on missing context; Breda does not approve or execute. | Codex |

**Sealed:** [date of crossing event]
**Sealer:** The Flame Architect
**Vault source:** `MoStar-Grid` (archive)
**Scan basis:** `provenance/SCAN.md`

## Disposition codes
- **CROSS** — eligible, lands in new tree
- **CROSS, FILTERED** — partial: schema/structure yes, data no
- **REVIEW** — eligible after content audit
- **REJECT** — does not cross
- **REJECT + ROTATE** — does not cross, and the value has been exposed; rotate

## Table

| Vault item | Disposition | New location | Note |
|---|---|---|---|
| `MOSTAR_DOCTRINE.md` | CROSS | `soul/canon/doctrine.md` | Re-seal under canon |
| `LICENSE-AFRICAN-SOVEREIGNTY.md` | CROSS | `LICENSE` | Verbatim |
| `README.md` (old) | REJECT | — | Rewrite per canon |
| `GRID.md`, `GRID_COMMANDS.txt` | REVIEW | `grid/README.md` | Carry concepts, rewrite |
| `Modelfile-DCX0-Mind` | CROSS | `dcx/dcx0-mind/Modelfile` | Diff-review for stale prompts |
| `Modelfile-DCX1-Soul` | CROSS | `dcx/dcx1-soul/Modelfile` | Verify Ibibio-corpus-gate present |
| `Modelfile-DCX2-Body` | CROSS | `dcx/dcx2-body/Modelfile` | Executor binding clause |
| `core/cognition/truth_engine/` | CROSS | `truth-engine/` | Elemental thresholds preserved |
| `memory/neo4j-mindgraph/` schema + migrations | CROSS, FILTERED | `mindgraph/schema/`, `grid/schema/` | `data/`, `import/data/` REJECTED |
| `memory/neo4j-mindgraph/data*` | REJECT | — | Contains seed_dashboard.bat leak |
| `scripts/ibibio_parser.py` | CROSS | `soul/ibibio/parser.py` | After review |
| `engines/idim-ikang/models/ibibio_modelfile_extension.txt` | CROSS | `soul/ibibio/ibibio_modelfile_extension.txt` | **Resolved:** Grid owns source of truth. IdimIkang imports from here. |
| `engines/idim-ikang/` (rest) | REJECT | — | Repo-bleed; belongs to IdimIkang repo |
| `frontend/` | DEFER | future `interface/` | Out of Phase 3.6 scope |
| `docs/*ARCHITECTURE*.md` | REJECT | — | Replaced by new diagrams |
| `archive/` | REJECT | — | _vault/ carries this |
| `cloudflared/`, `config/` | REJECT | — | Recreate from `.env.example` |
| `install_tools.sh`, `migrate_full.ps1`, `grid_setup.bat` | REJECT | — | Rewrite as `scripts/` originals |
| `run-ollama.sh` (fixed, commit 8ca01ec) | CROSS | `scripts/run-ollama.sh` | The verified-fixed version |
| `Dockerfile*` | REVIEW | `grid/docker/` | After secrets-audit |
| `docker-compose.yml` | REVIEW | `grid/docker/` | Strip env defaults to `${VAR}` only |
| `(2).env` | REJECT + ROTATE | — | All values compromised |
| `.ollama/.ollama/id_ed25519` | REJECT + ROTATE | — | Private key, on public GitHub |
| `*:Zone.Identifier` | REJECT | — | WSL cruft |
| `"Perfect, Overlord ⚡️ — this is exac.txt"` | REJECT | — | Chat transcript with secrets |
| `seed_dashboard.bat` (all) | REJECT | — | Leak source |
| `*swagger.json` with keys | REJECT | — | Regenerate spec, no committed examples |

## From local unpushed work (commits 455499da, cadf794c, 840bd3fb, 7959d289)

| Local item | New location |
|---|---|
| Phase 3.6 Runtime RFC | `rfcs/2026-04-phase-3.6-runtime-activation.md` |
| Phase 3 RFC | `rfcs/2026-04-phase-3-runtime.md` |
| Diagram: Phase Map | `architecture/phase-map.md` |
| Diagram: Cognitive Flow | `architecture/cognitive-flow.md` |
| Diagram: Woo Runtime Governance Flow | `architecture/woo-governance-flow.md` |
| Woo design (interpretation + resonance) | `woo/` subtree |
