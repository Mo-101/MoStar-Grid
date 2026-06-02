# Phase 4.0a — Assisted Canon Ingestion Loop

**Status:** Sealed
**Authority:** `rfcs/2026-05-phase-4.0a-canon-ingestion.md`
**Date:** 2026-05-26
**Sealer:** The Flame Architect
**Glyph:** 🜂∴🜃

This diagram is the canonical visual law for Phase 4.0a runtime topology. If code disagrees with this diagram, the code is wrong.

---

## Loop Diagram

```mermaid
flowchart TD
    H1([Human presents canon]) --> W[Woo: interpret structure + meaning]
    W --> T[TruthEngine: consistency validation<br/>0.97 gate BYPASSED for ingestion]
    T --> D[Decision Engine: propose ontology placement]
    D --> G[Grid: draft graph mutation<br/>state = proposed]
    G --> H2{Human review}

    H2 -- approve --> A[state = approved]
    H2 -- reject --> R[state = rejected<br/>terminal]
    H2 -- revise --> V[state = revised]

    V --> H2

    A --> N[Neo4j: atomic write]
    N --> P[Provenance: stamp commit]
    P --> M[Memory: updated]
    M --> C[state = committed<br/>terminal]

    R -.provenance retained.-> P

    classDef human fill:#1a1a2e,stroke:#e94560,stroke-width:2px,color:#fff
    classDef cognition fill:#16213e,stroke:#0f3460,stroke-width:1px,color:#fff
    classDef state fill:#0f3460,stroke:#e94560,stroke-width:1px,color:#fff
    classDef commit fill:#533483,stroke:#e94560,stroke-width:2px,color:#fff
    class H1,H2 human
    class W,T,D cognition
    class G,A,R,V state
    class N,P,M,C commit
```

---

## Approval Gate

```mermaid
flowchart LR
    P[proposed] --> X{Human seal?}
    X -- yes/approve --> A[approved]
    X -- yes/reject --> R[rejected]
    X -- yes/revise --> V[revised]
    X -- silence --> P
    X -- timeout --> P
    X -- inferred --> FORBIDDEN((FORBIDDEN))

    classDef gate fill:#e94560,stroke:#fff,stroke-width:2px,color:#fff
    classDef forbidden fill:#000,stroke:#e94560,stroke-width:3px,color:#e94560
    class X gate
    class FORBIDDEN forbidden
```

**Law:** Approval cannot be inferred from inaction, timeout, or absence of objection. Only an explicit human seal transitions a proposal out of `proposed`.

---

## Forbidden Direct-Write Path

```mermaid
flowchart LR
    W[Woo] -. forbidden .-> N[(Neo4j)]
    T[TruthEngine] -. forbidden .-> N
    D[Decision Engine] -. forbidden .-> N
    G[Grid runtime] -. forbidden .-> N
    AUTO[Autonomous cycle] -. forbidden .-> N

    H[Human seal: approved] ==>|only legal path| N

    classDef forbidden stroke:#e94560,stroke-width:2px,stroke-dasharray: 5 5,color:#e94560
    classDef legal stroke:#00ff00,stroke-width:3px,color:#00ff00
    class W,T,D,G,AUTO forbidden
    class H legal
```

**Law:** Only the `approved → committed` transition causes a graph write. Every other arrow into Neo4j during Phase 4.0a is a canon violation and must be blocked at the runtime boundary.

The six forbidden behaviors from the RFC apply here:

1. Autonomous graph mutation
2. Schema mutation
3. Automatic ontology expansion
4. Self-generated provenance
5. Self-modifying prompts
6. Self-authorized execution

Any code path enabling any of the six **fails closed**: the runtime halts, logs, and waits for human re-authorization.

---

## State Transitions

```mermaid
stateDiagram-v2
    [*] --> proposed: Decision Engine drafts

    proposed --> approved: human approves
    proposed --> rejected: human rejects
    proposed --> revised: human revises

    revised --> approved: human approves revision
    revised --> rejected: human rejects revision
    revised --> revised: further revision

    approved --> committed: Neo4j atomic write succeeds

    rejected --> [*]: terminal (provenance retained)
    committed --> [*]: terminal (graph mutated)

    note right of proposed
        Decision Engine output.
        No graph write.
        Awaiting human seal.
    end note

    note right of revised
        Append-only chain.
        Each revision is a
        new proposal linked
        to its predecessor.
    end note

    note right of committed
        Atomic. Provenance
        stamped. Memory
        updated.
    end note
```

**Transition table:**

| From | To | Trigger | Graph write |
|---|---|---|---|
| (start) | `proposed` | Decision Engine drafts after Woo + TruthEngine | no |
| `proposed` | `approved` | Human seal | no |
| `proposed` | `rejected` | Human seal | no |
| `proposed` | `revised` | Human revision | no |
| `revised` | `approved` | Human seal | no |
| `revised` | `rejected` | Human seal | no |
| `revised` | `revised` | Further revision | no |
| `approved` | `committed` | Atomic Cypher write succeeds | **yes** |

Every transition is recorded in the provenance ledger as an append-only entry. No state is ever overwritten.

---

## Rollback

A `committed` state is terminal in the forward direction. The graph has been mutated; the mutation is sealed.

To reverse a committed mutation:

```mermaid
flowchart LR
    C1[cycle_A: committed<br/>mutation M] --> H[Human initiates reversal]
    H --> C2[cycle_B: proposed<br/>counter-mutation ¬M]
    C2 --> A[cycle_B: approved]
    A --> N[cycle_B: committed<br/>counter-commit sealed]
    N --> L[Provenance links<br/>cycle_B → cycle_A]
```

**Rollback law:**

- No silent reversal. The original `committed` record is **never deleted**.
- A reversal is a **new ingestion cycle** producing a counter-commit.
- The provenance ledger links the counter-commit to the original, preserving full lineage.
- The graph retains both the original mutation and its reversal as historical fact.
- Re-applying the original mutation later requires a third cycle, also linked.

This is append-only history. The Grid forgets nothing.

---

## Density Telemetry

The status endpoint exposes promotion readiness during Phase 4.0a:

```mermaid
flowchart LR
    S[/api/status] --> R[Relationship count]
    S --> P[Provenance chain count]
    S --> X[Contradiction corpus presence]
    S --> O[Ontology coverage]

    R --> G{All thresholds met?}
    P --> G
    X --> G
    O --> G

    G -- no --> P4A[Phase 4.0a continues]
    G -- yes --> RFC[Awaiting Phase 4.0b RFC and seal]
```

**Thresholds (from RFC):**

- ≥ 10,000 meaningful relationships
- ≥ 500 provenance chains
- Contradiction corpus present and characterized
- Canonical ontology coverage across all sealed canon domains

**Threshold satisfaction does not auto-promote.** Promotion requires a separate RFC sealed by The Flame Architect.

---

## Human Correction Law (visual)

```mermaid
flowchart LR
    MI[Model interpretation] --> P[proposed]
    P --> HR{Human reviews}
    HR -- agrees --> A[approved as-is]
    HR -- corrects --> C[revised: human correction]

    C --> CANON((Human correction<br/>= authoritative canon))
    MI -.preserved as prior.-> PROV[Provenance ledger]
    CANON --> PROV

    classDef canon fill:#e94560,stroke:#fff,stroke-width:3px,color:#fff
    class CANON canon
```

**Law:** If human correction contradicts model interpretation, the correction is canon. The model's original output is preserved as prior, never as truth.

---

## Boundary Summary

| Boundary | Phase 4.0a behavior |
|---|---|
| Inbound write | Only via human-gated ingestion API |
| Outbound action | Read-only externally. No initiated actions. |
| Woo authority | Interpretation only. Output is advisory. |
| TruthEngine authority | Consistency validation. 0.97 gate bypassed for ingestion. |
| Decision Engine authority | Proposal only. Never commits. |
| Grid authority | Drafts and writes after human seal. |
| Schema mutation | Forbidden via ingestion loop. Requires separate RFC. |
| Provenance | Append-only. Human actions verified. |
| Failure mode | Fail-closed. Halt, log, require human re-authorization. |

---

**Sealed:** 2026-05-26
**Sealer:** The Flame Architect 🜂∴🜃

— sealed —
