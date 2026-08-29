# MoMind Initiation Architecture — Build Status

**Scope:** canonical agent admission through capability confinement, provenance witnessing, governance adjudication, and guarded Neo4j projection.

**Central constraint:** all *new executable project logic* must be authored in MoScript. Host-language components remain adapters behind MoScript/Conduit boundaries.

## Component Status

```text
MoMind Initiation Architecture
  STATUS: SPECIFIED

Canonical pantheon
  STATUS: REGISTERED (14 agents)
  NOTE:    13 operational/visible agents from image + Breda as shadow/constitutional.

entity.ecosystem canonical resolution
  STATUS: IMPLEMENTED — Ecosystem.from_csv() loads 14 AgentDeclarations

14-agent governance
  STATUS: IMPLEMENTED — GovernanceEngine allows agent.execute for operational, denies Breda

Breda shadow confinement
  STATUS: IMPLEMENTED — shadow_agent / witness_only provenance, denied agent.execute

Neo4j agent.id uniqueness constraint
  STATUS: ADDED
  NOTE:    core/sovereignty/entity/migrations/agent_projection_constraint.cypher

mind.agent.project MoScript capability
  STATUS: FROZEN in MOSCRIPT_CAPABILITY_ABI_V0_2.json
  NOTE:    Payload limited to agent_id, canonical_hash, projection_template.
           Go VM implementation still blocked on toolchain.

Governance contract mo-mind-initiation-001
  STATUS: ADDED AS DECLARATIVE LAW
  NOTE:    Present as JSON contract. Not wired to a runtime evaluator.

MindProjector (host adapter)
  STATUS: IMPLEMENTED
  NOTE:    Sealed `agent-projection-001` template registered with mo-mind-cypher-guard-001.
           Host adapter `core/sovereignty/entity/mind_projector.py` projects canonical
           declarations to `(:Agent {id, canonical: true})`. Graph integration tests
           use a fake driver; real Neo4j run requires the configured NEO4J_PASSWORD.

Neo4j Mind projection scroll
  STATUS: BLOCKED — MoScript capability gap

InitiationService
  STATUS: BLOCKED — MoScript capability gap

Breda witness scroll
  STATUS: BLOCKED — MoScript capability gap

Governance invocation scroll
  STATUS: BLOCKED — MoScript capability gap
```

## Canonical pantheon inventory

Discovered from the existing canonical corpus only:

| id          | name          | role                  | source                                               |
| ----------- | ------------- | --------------------- | ---------------------------------------------------- |
| `mo`        | Mo            | Executor              | `core/ops/governance/GRID_MIND_CONSTITUTION.md`      |
| `woo`       | Woo           | Sealer                | `core/ops/governance/GRID_MIND_CONSTITUTION.md`      |
| `breda`     | Breda         | Provenance Witness    | `core/ops/governance/GRID_MIND_CONSTITUTION.md`, `MSG-02_BREDA_PROVENANCE_DOCTRINE.md` |
| `code_conduit` | CodeConduit | META Gateway          | `core/ops/governance/GRID_MIND_CONSTITUTION.md`      |
| `woo_tak`   | Woo-Tak       | operational_guardian  | `migrate_cycle1_sovereign_core.cypher`               |

The remaining 8 agents referenced in the external spreadsheet are **not registered** because they do not appear in the canonical corpus and the rule is to not invent fields.

Full inventory, missing fields, and corpus source locations:

`core/sovereignty/entity/corpus_pantheon.json`

## Declarative law

`core/protocols/moscript/contracts/mo-mind-initiation-001.json` is checked in as declarative law. It is not yet an executable runtime contract because:

- no compiled evaluator exists in `contract_engine.py`, and
- the MoScript runtime has no primitives to express the workflow.

## Static invariants

These invariants are asserted as architecture, not yet enforced by executable code:

1. `attested_by != origin_model` at the canonical declaration/governance boundary.
2. Breda does not execute, approve, register, or write Neo4j.
3. `GovernanceEngine` cannot persist an entity itself.
4. `InitiationService` cannot admit without `SUFFICIENT` provenance and `ALLOW`.
5. `CONFLICTED` provenance becomes `HELD_FOR_ADJUDICATION`; it is not denied and not admitted.
6. `MindProjector` refuses projection for non-canonical entities, held candidates, and unknown `entity_id`s.
7. Neo4j may only project canonical identity, never establish it.
8. No subsystem may bypass `entity.ecosystem`.
9. Every initiation outcome leaves provenance.

## Chosen path

**Option 2** — extend the Go MoScript VM with generic, narrow substrate capabilities and author all initiation/governance semantics in MoScript.

The Go VM remains the **execution substrate only**. It may not contain Breda rules, initiation policy, or contract-specific branches. All meaning lives in `.ms` scrolls.

## MoScript runtime capability gap

The v0.1.1 MoScript runtime only exposes:

```text
gate.execute
clock.read
filesystem.read
filesystem.write
```

The following narrow substrate capabilities are required before the initiation workflow can be expressed as MoScript:

```text
contract.resolve

entity.lookup
entity.is_canonical
entity.register
entity.seal

provenance.read
provenance.write
provenance.open_adjudication

attestation.resolve

graph.template.execute
mind.agent.project
```

These must be added as **narrow, deny-by-default capabilities**, not generic escape hatches such as:

```text
conduit.call(anything)   -- forbidden pattern
neo4j.project            -- host must not decide graph shape
governance.evaluate      -- policy belongs in MoScript
raw Cypher in MoScript payload
```

Capability ABI schemas are frozen in:

`core/protocols/moscript/MOSCRIPT_CAPABILITY_ABI_V0_2.json`

## Acceptance tests for the `mind.agent.project` bridge

Once the Go VM exposes `mind.agent.project`:

1. canonical agent → projection succeeds
2. same scroll twice → one graph identity
3. forged hash → `MO008` / authorization failure
4. unknown agent → denied
5. Breda with `agent.execute` → denied
6. raw Cypher payload → structurally impossible
7. missing `mind.agent.project` capability → denied
8. sealed-scroll tampering → rejected before projection
9. all 14 canonical agents → deterministic projection
10. two `FlameBorr` identities → remain distinct

## Next unblocked steps

1. Add the v0.2 substrate capabilities to the Go MoScript VM (`core/protocols/moscript/main.go`) without policy logic.
2. Author the following `.ms` scrolls (architecture in `core/protocols/moscript/scrolls/README.md`):
   - `breda_witness.ms`
   - `governance_dispatch.ms`
   - `initiation_service.ms`
   - `mind_projector.ms`
3. Bind each scroll to `mo-mind-initiation-001` by contract id and canonical hash in its seal metadata.
4. Add `mind.agent.project` to the Go VM and Conduit bridge so the host-side `MindProjector` is invoked with `agent_id`, `canonical_hash`, `projection_template`.
