# MoScript Initiation Scrolls

This directory will contain the executable MoScript scrolls for the MoMind agent initiation architecture.

> **Status:** blocked on `MOSCRIPT_CAPABILITY_ABI_V0_2` support in the Go MoScript VM.
> The host Go runtime currently exposes only:
>
> ```text
> gate.execute
> clock.read
> filesystem.read
> filesystem.write
> ```
>
> All governance meaning below will be authored in `.ms` once the required substrate capabilities are wired.

## Authority split

| Layer | Responsibility | Language |
|-------|----------------|----------|
| Go VM | execution, capability dispatch, limits, trust substrate | Go |
| MoScript scrolls | governance logic, state machine, admission policy | MoScript `.ms` |
| JSON contracts | declarative law, versioned policy identity | JSON |

## Scrolls

### `breda_witness.ms`

- Receives a candidate submission.
- Resolves `mo-mind-initiation-001` via `contract.resolve`.
- Inspects candidate declaration, provenance, and attestation via `entity.lookup`, `provenance.read`, `attestation.resolve`.
- Returns a `ProvenanceAssessment` in `{SUFFICIENT, CONFLICTED, INSUFFICIENT, INDETERMINATE, WITHDRAWN}`.
- **Does not** register, approve, or write to Neo4j.
- Sealed capability manifest must **not** include:
  - `entity.register`
  - `provenance.open_adjudication`
  - `graph.template.execute`

### `governance_dispatch.ms`

- Loads `mo-mind-initiation-001` by contract id + canonical hash.
- Computes admission from Breda assessment, declaration validity, and attestation independence.
- Returns `ALLOW`, `DENY`, or `HELD`.
- Does not execute host policy branches; all meaning is in the scroll.

### `initiation_service.ms`

- Receives a candidate.
- Requests `breda_witness.ms`.
- Routes `CONFLICTED` to `provenance.open_adjudication` and sets state to `HELD_FOR_ADJUDICATION`.
- For `SUFFICIENT`, requests `governance_dispatch.ms`.
- On `ALLOW`, calls `entity.register` and `entity.seal`.
- Emits `provenance.write` for every terminal branch.
- **Does not** write Cypher or decide graph policy.

### `mind_projector.ms`

- Receives an `entity_id`.
- Calls `entity.is_canonical`.
- On `true`, calls `mind.agent.project` with `agent_id`, `canonical_hash`, and `projection_template: "agent-projection-001"`.
- Fails closed for non-canonical, held, or unknown entities.

## Capability manifests

### `breda_witness.ms`

```text
contract.resolve
entity.lookup
provenance.read
attestation.resolve
```

### `initiation_service.ms`

```text
contract.resolve
entity.lookup
provenance.read
provenance.write
provenance.open_adjudication
entity.register
entity.seal
attestation.resolve
```

### `mind_projector.ms`

```text
entity.lookup
entity.is_canonical
mind.agent.project
```

## Contract binding

Each scroll must include the canonical contract identity and hash in its seal metadata so the executable scroll and declarative law cannot silently drift:

```text
contract_id = "mo-mind-initiation-001"
contract_hash = <sha256 of core/protocols/moscript/contracts/mo-mind-initiation-001.json>
```

## Runtime gap

See `core/ops/status/MOMIND_INITIATION_ARCHITECTURE_STATUS.md` for the exact list of missing Go VM capabilities.
