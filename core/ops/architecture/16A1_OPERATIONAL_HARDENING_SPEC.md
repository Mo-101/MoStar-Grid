# Phase 16A: Operational Hardening Specification

**Status:** Live verification passed (16A5, 2026-06-22)  
**Last Updated:** 2026-06-22  
**Scope:** Telemetry aggregation, anomaly detection, control-plane gating, role-enforcement consolidation  

---

## 1. Core Principles

### 1.1 Observation vs Enforcement Separation

**Hard Rule:** Monitoring may suggest; control-plane enforcement must be explicit, explainable, and auditable.

- **Telemetry Layer** (16A3_telemetry_alerter.py): Computes signals, emits warnings/events, **makes zero state changes**
- **Control Layer** (16A4_control_plane_stabilizer.py): Applies gated enforcement only when policy permits, **must be traceable**

**No cross-pollution:** Alerting noise must never trigger hard locks without an explicit policy decision.

### 1.2 Enforcement Levels (Escalation Hierarchy)

All control-plane decisions map to exactly one level. Each level defines what actions are permitted:

| Level | Definition | Permitted Actions | Examples |
|-------|-----------|-------------------|----------|
| `INFO` | Baseline monitoring active | Log events, emit metrics, audit trails | Normal operation, metrics collection |
| `WARN` | Alert conditions detected | Log warnings, raise telemetry events, increase scrutiny | Single-point anomaly, temporary spike |
| `ELEVATED` | Pattern emerging; additional checks engaged | Require secondary checks, increase validation depth, mandate approval flows | Resonance decay trending up, multiple warnings in window |
| `RESTRICTED` | Enforcement boundaries tightened | Deny non-critical execution classes, require explicit whitelist, apply rate limits | Persistent pattern, policy threshold crossed |
| `LOCKED` | Hard stop for protected surfaces | Explicit hard block, require manual override, escalate to ThroneLock | Cascading failures, critical threshold hit, rollback triggered |

**Transitions must be explicitly logged** with crossing reason, timestamp, and recovery condition.

### 1.3 Enforcement Hierarchy

Control decisions respect this precedence (highest to lowest):

1. **ThroneLock** (active role override, from authoritative source)
2. **Explicit policy** (config-defined boundaries)
3. **Resonance decay** (pattern-based gating)
4. **Telemetry alerts** (observation only; does NOT trigger restrictions)

**Never apply restriction from telemetry alone.** Telemetry feeds policy; policy decides enforcement.

---

## 2. Resonance Decay Model

### 2.1 Requirements

Resonance posture must be:

- **Rolling window** (not cumulative lifetime)
- **Weighted by recency** (recent failures matter more)
- **Event-type-weighted** (critical events weigh heavier)
- **Explicitly recoverable** (decay/relaxation must trigger automatically)
- **Fully debuggable** (store state, contributing events, decay reason)

### 2.2 Computation

**Formula:**

```
resonance_score = Σ(event_weight × decay_factor(age)) / time_window_length

where:
  event_weight ∈ [0.1 (info), 0.5 (warn), 1.0 (elevated), 2.0 (restricted), 5.0 (locked)]
  decay_factor(age) = exp(-age_seconds / half_life_seconds)
  time_window_length = 3600 seconds (configurable)
  half_life = 600 seconds (events lose 50% weight after 10 min, configurable)
```

**Thresholds:**

- `score < 0.2`: Level `INFO` (green)
- `0.2 ≤ score < 0.5`: Level `WARN` (yellow)
- `0.5 ≤ score < 1.5`: Level `ELEVATED` (amber)
- `1.5 ≤ score < 3.0`: Level `RESTRICTED` (orange)
- `score ≥ 3.0`: Level `LOCKED` (red)

### 2.3 State Tracking

Store in `control_plane_resonance_state` table:

```sql
CREATE TABLE control_plane_resonance_state (
    id UUID PRIMARY KEY,
    component_id VARCHAR NOT NULL,
    current_score FLOAT NOT NULL,
    level VARCHAR NOT NULL,  -- INFO, WARN, ELEVATED, RESTRICTED, LOCKED
    contributing_events JSONB NOT NULL,  -- array of {event_id, type, weight, timestamp}
    decay_reason VARCHAR,  -- "age", "recovery", "manual_reset"
    threshold_crossed_at TIMESTAMP,
    last_computed TIMESTAMP NOT NULL,
    previous_level VARCHAR,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### 2.4 Recovery Logic

Automatic relaxation:

- When `score` falls below threshold for current level, downgrade to next lower level
- Example: `RESTRICTED` → `ELEVATED` when score drops below 1.5
- Log every transition with reason and timestamp
- **Never skip levels on relaxation** (prevents thrashing)

**Manual reset:**

- Explicit audit event: `RESONANCE_MANUAL_RESET`
- Requires role permission
- Sets level to `INFO`, stores reason

---

## 3. ThroneLock Consolidation

### 3.1 Single Source of Truth

**Authoritative role registry:** Neo4j (graph_role, role_active_marker)

**Mirrors/Audit:**

- Neon read replica (for fast query during enforcement)
- Config file (bootstrap/emergency fallback only)

**Resolution precedence:**

1. Neo4j active graph_role with current timestamp validity
2. Neon replica (if Neo4j unavailable, with staleness warning)
3. Config fallback (with explicit manual-override audit)

**Never resolve roles from multiple places dynamically** without explicit precedence in spec.

### 3.2 Active Role Markers

Neo4j role enforcement:

```cypher
MATCH (r:graph_role {id: $role_id})
WHERE r.is_active = TRUE AND r.validity_end > datetime.realtime.transaction()
RETURN r.id, r.permissions, r.enforcement_level
```

Audit on every resolution:

- Role ID resolved
- Source used (Neo4j / Neon / Config)
- Enforcement level applied
- Timestamp

---

## 4. Telemetry Aggregation

### 4.1 Metric Sources

Aggregate from (in priority order):

1. `graph_audit_event` — control-plane decisions, policy changes
2. `agent_run_log` — agent execution health
3. `decision_run_log` — decision engine state
4. `moscript_registry` — MoScript execution patterns
5. `woo_interpretation_log` — Woo denial/warning spikes (resonance-relevant)

### 4.2 Query Building (16A2)

`telemetry_query_builder.py` constructs safe, composable queries:

- Parameterized event types
- Rolling window queries
- Aggregation by component/level
- Decay factor computation
- Cache-friendly structure

All queries must:

- Include timestamp filtering
- Support batch aggregation
- Be explainable (include reasoning in output)
- Have configurable time windows

---

## 5. Alerter (16A3)

### 5.1 Responsibility

**Observation only. No enforcement.**

- Monitor telemetry streams
- Detect anomalies (spike, trend, threshold)
- Emit telemetry events to `graph_audit_event`
- Compute resonance scores
- **Make zero control-plane changes**

### 5.2 Event Types

Alerter emits (all map to `graph_audit_event`):

- `TELEMETRY_ALERT_RAISED` — anomaly detected
- `ANOMALY_SPIKE` — sudden metric spike
- `ANOMALY_TREND` — sustained pattern
- `ANOMALY_THRESHOLD` — explicit boundary crossed
- `RESONANCE_SCORE_UPDATED` — score recalculated
- `RESONANCE_DECAY_APPLIED` — decay applied

### 5.3 Dry-Run Mode

```bash
python 16A3_telemetry_alerter.py --dry-run
```

- Compute all signals
- Report what events WOULD be emitted
- Make zero database writes
- Output summary of detected anomalies

---

## 6. Stabilizer (16A4)

### 6.1 Responsibility

**Policy-driven enforcement only.**

- Read telemetry state and resonance score
- Consult active ThroneLock roles
- Apply enforcement boundaries (deny execution, rate-limit, require approval)
- Audit every control decision
- Support explicit escalation/de-escalation

### 6.2 Control Actions

Enforcer applies (by level):

| Level | Actions |
|-------|---------|
| `INFO` | None (pass-through) |
| `WARN` | None (pass-through; alerter raises events) |
| `ELEVATED` | Require secondary auth on sensitive ops; mandate approval flow |
| `RESTRICTED` | Deny non-critical execution classes; require explicit whitelist |
| `LOCKED` | Hard block unless ThroneLock override active |

### 6.3 Events Emitted

- `CONTROL_PLANE_RESTRICTED` — enforcement boundary applied
- `CONTROL_PLANE_LOCKED` — hard block applied
- `THRONELOCK_ROLE_ENFORCED` — active role triggered exception
- `CONTROL_PLANE_RELAXED` — enforcement downgraded

### 6.4 Dry-Run Mode

```bash
python 16A4_control_plane_stabilizer.py --dry-run
```

- Evaluate all policies
- Report what enforcement WOULD be applied
- Make zero control-plane state changes
- Output enforcement decision tree

---

## 7. Verifier (16A5)

### 7.1 Normative closure checks

A closable result requires `--live`; a dry-run-only verifier execution must
report an overall failure.

1. **CHK_001 — Metric Aggregation and Alert Dispatch**
   - Execute parameterized queries against all five live Neon sources
   - Prove anomaly detection on a known bad pattern
   - Persist and read back alert/resonance audits
2. **CHK_002 — Policy Application and ThroneLock Precedence**
   - Load `core/ops/config/enforcement_policy.yaml`
   - Exercise Aura as the authoritative source; fall back only on failure
   - Persist both the source decision and policy action
3. **CHK_003 — Persisted Audit Trail Completeness**
   - Read audits back from Neon with trace, levels, writer, and dry-run fields
4. **CHK_004 — Dry-Run No-Op Safety**
   - Compare audit and resonance-state snapshots before and after both dry-run paths
5. **CHK_005 — Recovery and De-escalation**
   - Persist `LOCKED -> RESTRICTED -> ELEVATED -> WARN -> INFO` one step at a time
   - Apply hysteresis, record recovery reasons, and audit manual reset

### 7.2 Historical check description (superseded)

1. **Alerter signal integrity**
   - Telemetry queries return valid data
   - Anomaly detection triggers on known bad patterns
   - Events emit correctly

2. **Enforcer policy application**
   - Policies apply in correct precedence
   - Enforcement levels transition correctly
   - No orphaned locks

3. **Audit trail completeness**
   - Every decision logged
   - Events traceable to source
   - Recovery conditions detectable

### 7.3 Historical additions (superseded)

1. **Dry-run safety** (CRITICAL)
   - Run alerter in `--dry-run`; verify no events written
   - Run stabilizer in `--dry-run`; verify no control state changed
   - Thresholds trigger predicted actions
   - Dry-run output matches live output (minus side effects)

2. **Recovery and de-escalation**
   - When alert conditions clear, stabilizer relaxes automatically
   - Transitions logged explicitly (old level → new level)
   - Manual reset works and audits correctly
   - No stuck locks after recovery

---

## 8. Audit Events Table Schema

```sql
CREATE TABLE graph_audit_event (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_type VARCHAR NOT NULL,  -- see event types above
    component_id VARCHAR NOT NULL,
    actor_id VARCHAR,  -- system, role_id, or NULL
    source_level VARCHAR NOT NULL,  -- INFO, WARN, ELEVATED, RESTRICTED, LOCKED
    target_level VARCHAR,  -- if transition event
    policy_enforced VARCHAR,  -- if policy-driven
    event_data JSONB,  -- supporting detail
    trace_id VARCHAR,  -- for linking related events
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    created_by_component VARCHAR NOT NULL,  -- 16A3, 16A4, manual, etc.
    is_dry_run BOOLEAN DEFAULT FALSE
);

CREATE INDEX ON graph_audit_event(event_type, created_at DESC);
CREATE INDEX ON graph_audit_event(component_id, created_at DESC);
CREATE INDEX ON graph_audit_event(source_level, created_at DESC);
```

---

## 9. Configuration

### 9.1 Environment Variables

```bash
# Resonance parameters
RESONANCE_WINDOW_SECONDS=3600
RESONANCE_HALF_LIFE_SECONDS=600
RESONANCE_THRESHOLD_WARN=0.2
RESONANCE_THRESHOLD_ELEVATED=0.5
RESONANCE_THRESHOLD_RESTRICTED=1.5
RESONANCE_THRESHOLD_LOCKED=3.0

# Telemetry aggregation
TELEMETRY_BATCH_SIZE=1000
TELEMETRY_QUERY_TIMEOUT_MS=5000

# ThroneLock
THRONELOCK_SOURCE=neo4j  # neo4j, neon, config
THRONELOCK_NEO4J_FALLBACK=neon
THRONELOCK_NEO4J_STALENESS_WARNING_MS=60000

# Enforcement
ENFORCEMENT_ENABLED=true
ENFORCEMENT_DRY_RUN=false

# Alerting
ALERTER_INTERVAL_SECONDS=30
ALERTER_DRY_RUN=false
```

### 9.2 Policy File

```yaml
# enforcement_policy.yaml
policies:
  agent_execution:
    info: null  # no restrictions
    warn: null
    elevated:
      require_approval: true
      approval_timeout_seconds: 300
    restricted:
      deny_non_critical: true
      critical_classes: ["system", "security", "recovery"]
    locked:
      hard_block: true
      require_thronelock_override: true

  decision_engine:
    restricted:
      require_secondary_auth: true
      rate_limit_per_minute: 30
    locked:
      hard_block: true

  moscript_registry:
    elevated:
      require_whitelist: true
      audit_all_executions: true
    restricted:
      deny_experimental: true
    locked:
      hard_block: true
```

---

## 10. Implementation Sequence

1. **16A1** ← You are here (spec locked)
2. **16A2** Create `telemetry_query_builder.py`
3. **16A3** Create `telemetry_alerter.py` (observation)
4. **16A4** Create `control_plane_stabilizer.py` (enforcement)
5. **16A5** Create `verify_operational_hardening.py` (validation + dry-run + recovery)
6. **16A6** (future) Wire to live runtime surfaces

---

## 11. Success Criteria

- [x] Spec approved and locked
- [x] Alerter computes signals, emits zero enforcement
- [x] Stabilizer applies policy-driven enforcement only
- [x] Resonance decay is rolling-window, recoverable, debuggable
- [x] ThroneLock uses single source of truth
- [x] Dry-run mode works on both alerter and stabilizer
- [x] All transitions logged with reason
- [x] Verifier passes all 5 checks live
- [x] No control-plane state change without audit event
- [x] Recovery/de-escalation tested and working

---

## 12. Hard Rules (Non-Negotiable)

1. **Monitoring may suggest; control-plane enforcement must be explicit, explainable, and auditable.**
2. **Telemetry layer (16A3) makes zero state changes.**
3. **Control layer (16A4) applies only policy-permitted actions.**
4. **Every enforcement decision is audited.**
5. **Resonance decay is rolling-window with automatic relaxation.**
6. **ThroneLock resolves from single source of truth.**
7. **Dry-run mode changes nothing.**

---

**Closure Evidence:** `16A5_LIVE_VERIFICATION.md`
