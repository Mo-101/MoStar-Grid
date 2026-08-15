# Governance Constitution — Neo4j

Source of truth for the MoStar Grid adjudication constitution.

## Provenance: this is a reconciliation

**Git did not originally create these objects.** On 2026-08-15 the live Neo4j
database was found to hold the full adjudication constitution — 208 labels,
140 relationship types, 13 uniqueness constraints, 19 indexes — while
`core/ops/migrations/` contained only `001_sovereign_governance.sql`
(Postgres). Production schema was ahead of source control, applied
out-of-band, with no versioned origin.

`migrations/000_current_governance_baseline.cypher` was read back from the
live database (`SHOW CONSTRAINTS` / `SHOW INDEXES`) and rewritten in
idempotent form. It reproduces the structure on a fresh database and is a
no-op against the current one. It contains **schema only** — no instance
data, no synthetic fixtures, no credentials.

## Layout

```
migrations/    idempotent structural setup (constraints, indexes)
transactions/  write shapes the application is permitted to use
gates/         constitutional invariants (positive + negative witnesses)
constitution/  authoritative vocabularies (relationships, labels, statuses)
```

Intentionally untyped discovery queries live in `core/ops/audit/neo4j/` and
are **exempt** from the governance lint.

## Enforcement

Source lint — `core/ops/scripts/validate_governance_cypher.py --all`:

| pattern | verdict |
|---|---|
| `-[]->`, `-[r]->`, `-[_TO]->` | reject — untyped |
| `-[:PROMOTES]->` | reject — not in vocabulary |
| `-[:PROMOTED]->`, `-[r:ASSIGNED_TO]->` | accept |

The closed vocabulary has **27 members** (`constitution/relationship_types.py`).
Adding one is a constitutional amendment: source change, vocabulary change,
tests, migration, review.

Source lint cannot see relationships created out-of-band. Its runtime
counterpart is `core/ops/audit/neo4j/governance_vocabulary_drift.cypher`,
which asks the live graph the same question. Both must be run.

## Witness doctrine

Every critical invariant needs **two** witnesses:

- **positive** — the required valid path exists (`promotion_presence`)
- **negative** — no invalid path exists (`promotion_absence_of_bad`)

Gate A alone stays green when a forged promotion sits *alongside* a valid
one. Gate B is what catches it. The decisive fixture is **one valid + one
forged promotion**: A must PASS while B must FAIL. If both pass there, the
pair is not doing distinct work.

### Threat class: semantic false-positive

> An operation executes successfully and its test passes, while the
> executable semantics are weaker or different from the stated invariant.

Instances found in this codebase on 2026-08-15:

1. `MATCH (n {synthetic:true})` returned zero rows and looked like
   "production clean". The property had never been written to any node
   (Neo4j warned `01N52`). Zero rows meant *nobody has ever tagged
   anything*. See `gates/synthetic_isolation.cypher`.
2. `-[r]->` in a promotion gate matches every relationship type, so the gate
   reports "no illegal promotions" while constraining nothing.
3. `PROMOTES` for `PROMOTED` parses and runs green over an empty match.

## Status as of 2026-08-15

Gates A, B, C, D all pass — **but over one synthetic claim**:

| label | total | `:test:` | `synthetic=true` |
|---|---:|---:|---:|
| Claim | 1 | 1 | 0 |
| CanonicalPromotion | 1 | 1 | 0 |
| AuthorizationDecision | 0 | 0 | 0 |
| Testimony | 0 | 0 | 0 |

Non-test accepted claims: **0**. The gates are verified as *implementations*;
the constitution is **not yet stress-validated**. Negative fixtures (step 8)
must prove each gate can FAIL before green means anything.

Separation of duties is **logical only** — asserted inside gate predicates,
not enforced by Neo4j RBAC. Any principal with write access can bypass it
until steps 9–10 land.

## Execution order

```
5.  Commit governance constitution into repo        <- this directory
6.  Scope relationship guard to governance paths    <- done
7.  Enforce closed relationship vocabulary          <- done
8.  Add constitutional negative-fixture tests
9.  Establish Neo4j role/service separation
10. Make Browser governance access read-only
11. Tag/archive/purge synthetic state (maintenance identity)
12. Re-run complete governance gates
13. Rotate/revoke remaining compromised credentials
14. Permission/storage redesign
```

Steps 9–10 precede 11 deliberately: tagging is a governance write, so doing
it before role separation would make the first act under the new constitution
a violation of it.
