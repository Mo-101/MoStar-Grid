# Phase 16B: Runtime Enforcement Attachment

**Status:** Attached; focused verification passed  
**Depends on:** Phase 16A closed, live verifier 5/5

## 1. Scope

Attach the verified 16A state to the active `GridOrchestrator` execution spine:

| Surface | Component state | Policy branch | Interception point |
|---|---|---|---|
| Agents/DCX | `agents` | `agent_execution` | Before `dcx.think()` |
| Mo↔Woo nexus | `mo_woo_nexus` | `mo_woo_nexus` | Before Woo judgment and interpretation |
| Decision engine | `decision_engine` | `decision_engine` | Before placement ranking |
| MoScripts | `moscript_registry` | `moscript_registry` | Before each script fires |

## 2. Shared contract

Every surface calls one gate with `surface`, `operation`, and explicit context.
The gate reads `control_plane_resonance_state`, resolves the configured actions,
returns a structured decision, and persists `RUNTIME_ENFORCEMENT_ALLOWED` or
`RUNTIME_ENFORCEMENT_DENIED` to `graph_audit_event`.

Decision fields are component, policy branch, level, actions, operation,
allowed/denied, reason, trace ID, and timestamp.

## 3. Action semantics

- `INFO` and `WARN`: pass through.
- `hard_block`: always deny.
- `deny_non_critical`: require `critical=true`.
- `require_approval`: require `approved=true`.
- `require_secondary_auth`: require `secondary_auth=true`.
- Whitelist actions require the operation/runtime ID in the supplied whitelist.
- `deny_experimental`: deny `experimental=true`.
- `deny_side_effects`: allow governance-only Woo work, deny side effects.
- Logging, scrutiny, validation-depth, and rate-limit actions remain returned
  obligations; rate-limit mechanics are a separate bounded phase.

## 4. Failure behavior

When enforcement is enabled, a state-store error denies execution. A missing state
row is valid `INFO`; a database error is not. Attached production surfaces expose
no local dry-run bypass.

## 5. Acceptance

1. All four interception points have focused tests.
2. `INFO` passes and `LOCKED` blocks all four before the underlying call.
3. `RESTRICTED` applies criticality, approval, whitelist, and side-effect rules.
4. Every allow/deny evaluation is audited with its returned trace ID.
5. Quarantined non-16A failures are untouched and excluded from acceptance.

## 6. Verification evidence

- Focused runtime suite: `11 passed`
- Phase 16A regression verifier after attachment: `5/5 PASS`, live mode
- Live runtime probe: `mo_woo_nexus`, level `INFO`, allowed, persisted as
  `RUNTIME_ENFORCEMENT_ALLOWED`, then cleaned up
