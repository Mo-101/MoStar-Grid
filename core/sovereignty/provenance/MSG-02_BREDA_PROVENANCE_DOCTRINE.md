# MSG-02 Breda Provenance Doctrine

**Date:** 2026-06-07
**Status:** ACTIVE DOCTRINE - implementation pending
**Role:** provenance witness and trust classifier

## Prime Rule

Breda does not execute.

Breda does not approve.

Breda witnesses provenance and reports whether a moment, action, import, or
claim has enough context to be trusted by the Grid.

## Doctrine Statement

No Grid memory, moment, route, agent response, or imported archive artifact may
be treated as operational truth unless its provenance class is explicit.

Unknown origin is not neutral. Unknown origin is a risk state.

## Required Provenance Fields

Breda expects these fields on persistent `MoStarMoment` records:

```text
source_type
verification_status
operational_trust
seal
source
created_by
```

If any required field is missing, Breda must return:

```text
NEEDS_CONTEXT
```

or:

```text
DENY
```

depending on whether the caller is asking for display/reference use or
operational action.

## Verdicts

```text
APPROVE        provenance is explicit, verified, and fit for requested use
WARN           provenance is explicit but not strong enough for full trust
DENY           provenance is missing, contradictory, or unsafe for action
NEEDS_CONTEXT  more source, seal, or human attestation is required
QUARANTINE     artifact contains exposed secrets, corrupted lineage, or unsafe import material
```

## Trust Rules

```text
human_attested + verified + operational
  may support operational Grid behavior

imported_archive + unverified + reference
  may be displayed or studied, but not used as operational truth

runtime_generated + synthetic + simulation
  may support UI/runtime narration, but not canon

ai_generated + unverified + reference
  may suggest, never seal

live_api + verified
  may support runtime telemetry only for the observed source and timestamp
```

## Failure Mode

Breda fails closed.

```text
missing provenance     -> NEEDS_CONTEXT or DENY
ambiguous source       -> NEEDS_CONTEXT
conflicting lineage    -> DENY
secret exposure        -> QUARANTINE
unsealed human claim   -> WARN or NEEDS_CONTEXT
```

Silent approval is forbidden.

## Relationship to Woo and TruthEngine

```text
Woo interprets resonance and meaning.
TruthEngine governs consistency and contradiction.
Breda witnesses provenance and trust fitness.
Grid executes only after required gates pass.
```

Breda is a gate input, not the final sovereign actor.

## P4-009 Seal Condition

P4-009 is complete when:

```text
MSG-02 doctrine is recorded
Breda verdict vocabulary is fixed
required provenance fields are fixed
missing-context behavior is fail-closed
runtime integration is tracked as later implementation work
```

