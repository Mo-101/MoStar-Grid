# soul/ibibio/

**Source of truth for the Ibibio language layer across the entire MoStar ecosystem.**

This folder is the single canonical home of the Ibibio corpus. There is no other authoritative copy. All downstream systems consume from here.

## Contents

- 405 IbibioWord entries
- 43 tone patterns
- Audio path bindings
- `ibibio_modelfile_extension.txt` — model-side prompt extension for DCX1-Soul and the Idim Ikang model

## Source-of-truth contract

| Repository | Relationship to this folder |
|---|---|
| `mostar-grid-core` | **owns** — this is the canonical home |
| `IdimIkang-main-1` | **imports** — consumes `ibibio_modelfile_extension.txt` from here |
| Any future system needing Ibibio data | **imports** from here, never forks |

## Distribution policy

Downstream consumers must **not** fork the corpus. They have two legal paths:

1. **Submodule** this repo's `soul/ibibio/` into their tree, pinned to a commit hash.
2. **Vendor** a frozen snapshot, with a sibling `IBIBIO_SOURCE.md` in the consumer recording:
   - the source commit hash
   - the date of the snapshot
   - the sealer's identifier

Corrections to the corpus flow back here first via PR, then downstream re-syncs.

## DCX1-Soul gate

The DCX1-Soul model (`dcx/dcx1-soul/Modelfile`) is bound by a hard rule: it must not generate Ibibio it cannot verify against the Neo4j corpus loaded from this folder. The verification path is non-optional.
