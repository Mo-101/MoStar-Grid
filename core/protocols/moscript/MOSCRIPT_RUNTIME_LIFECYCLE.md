# MoScript Runtime Lifecycle Specification

## 1. Planes

MoScript execution is stratified into five trust planes:

| Plane | Responsibility | Primary Artifacts |
|-------|----------------|-------------------|
| Developer | Editor, schema, error reporting | `moscript.tsx`, `moscripts-schema.ts` |
| Language | Lexer, parser, compiler, glyph ABI | `main.go`, `MOSCRIPT_GLYPH_ABI_V0_1.json` |
| Artifact | Scrolls, manifests, sealed contracts | `.ms`, `.mobc`, `.moscroll`, `contracts.manifest.json` |
| Governance | Contract registry, engine, decisions | `ContractRegistry`, `GovernanceEngine`, `ContractDecision` |
| Control | Orchestrator, API, runtime manager | `orchestrator.py`, `RuntimeManager` |
| Evidence | Hashes, status, provenance, audit | `MOSCRIPT_RUNTIME_IMPLEMENTATION_MAP.json` |

The Glyph ABI defines what may be *expressed*.
The Capability ABI defines what may be *requested*.
The Contracts define what is *permitted now*.
The Runtime Manager decides whether execution actually *happens*.

Language validity does **not** imply execution authority.

## 2. Lifecycle States

```
DISCOVERED
    │
    ▼
VERIFIED          ←─ artifact passes compiler / sealer / hash checks
    │
    ▼
GOVERNED          ←─ all governing contracts return ALLOW / STAGE_CANDIDATE
    │
    ▼
STAGED            ←─ artifact staged in workspace
    │
    ▼
RUNNING           ←─ Go runtime invoked
    │
    ▼
COMPLETED ────────▶ ATTEST ────────▶ AUDIT

Terminal failure states:
    DENIED
    QUARANTINED
    FAILED
```

## 3. Manager Duties

`RuntimeManager` is the fail-closed execution supervisor. It must:

1. **Discover**: identify artifact kind (`.ms`, `.mobc`, `.moscroll`).
2. **Verify**: compile or verify sealed artifact; extract `program_hash` and required capabilities.
3. **Govern**: run `ContractRegistry` freeze and `GovernanceEngine` evaluation.
4. **Authorize**: require explicit contract `ALLOW` before any execution.
5. **Stage**: stage the artifact in a capability-bounded workspace.
6. **Execute**: invoke the Go runtime (`moscript run`, `moscript run-scroll`) with allowed capabilities.
7. **Attest**: produce deterministic output and provenance.
8. **Audit**: append immutable evidence and transition log.

Every transition is fail-closed. A `DENY`, `ERROR`, or `QUARANTINE` decision terminates the lifecycle.
