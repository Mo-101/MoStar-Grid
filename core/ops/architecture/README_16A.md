# Phase 16A: Operational Hardening

**Status:** Phase definition complete  
**Locked Decisions:** Core runtimes live; next layer is telemetry, alerting, control-plane consolidation  
**Core Principle:** Monitoring may suggest; control-plane enforcement must be explicit, explainable, and auditable.

---

## Overview

Phase 16A hardens MoStar Grid operational posture by:

1. **Observing** telemetry signals (16A3)
2. **Enforcing** policy-driven boundaries (16A4)
3. **Auditing** every decision (16A1, 16A5)
4. **Recovering** gracefully when conditions improve (16A5)

The architecture enforces strict separation: **alerting suggests; only policy-permitted actions are enforced.**

---

## File Structure

### Specification & Configuration
- **[16A1_OPERATIONAL_HARDENING_SPEC.md](architecture/16A1_OPERATIONAL_HARDENING_SPEC.md)** — Master specification with enforcement levels, resonance model, ThroneLock consolidation
- **[enforcement_policy.yaml](config/enforcement_policy.yaml)** — Policy rules for each component/level

### Implementation Modules
- **[16A2_telemetry_query_builder.py](scripts/16A2_telemetry_query_builder.py)** — Composable query building with decay computation
- **[16A3_telemetry_alerter.py](scripts/16A3_telemetry_alerter.py)** — Observation only; detects anomalies, emits events
- **[16A4_control_plane_stabilizer.py](scripts/16A4_control_plane_stabilizer.py)** — Policy-driven enforcement; applies boundaries
- **[16A5_verify_operational_hardening.py](scripts/16A5_verify_operational_hardening.py)** — Comprehensive verifier with 5 checks including dry-run and recovery

---

## Architecture: Observation vs Enforcement

```
┌──────────────────────────────────────────────────────────────────┐
│ Telemetry Layer (16A3): Observation Only                         │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ Sources:                                                │    │
│  │  • graph_audit_event                                    │    │
│  │  • agent_run_log                                        │    │
│  │  • decision_run_log                                     │    │
│  │  • moscript_registry                                    │    │
│  │  • woo_interpretation_log                               │    │
│  └─────────────────────────────────────────────────────────┘    │
│                             │                                    │
│                             ▼                                    │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ Anomaly Detection:                                      │    │
│  │  • Spike detector                                       │    │
│  │  • Trend detector                                       │    │
│  │  • Threshold detector                                   │    │
│  └─────────────────────────────────────────────────────────┘    │
│                             │                                    │
│                             ▼                                    │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ Resonance Score Computation (rolling window):           │    │
│  │  score = Σ(event_weight × decay_factor(age))           │    │
│  └─────────────────────────────────────────────────────────┘    │
│                             │                                    │
│                             ▼                                    │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ Emit Events to graph_audit_event (ZERO enforcement):   │    │
│  │  • TELEMETRY_ALERT_RAISED                               │    │
│  │  • ANOMALY_SPIKE / _TREND / _THRESHOLD                  │    │
│  │  • RESONANCE_SCORE_UPDATED                              │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│  ⚠️  HARD RULE: Alerter makes ZERO control-plane changes       │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌──────────────────────────────────────────────────────────────────┐
│ Control-Plane Layer (16A4): Enforcement Only                    │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ Policy Engine:                                          │    │
│  │  • Read enforcement_policy.yaml                         │    │
│  │  • Map level → allowed actions                          │    │
│  │  • Verify actions are explicitly permitted              │    │
│  └─────────────────────────────────────────────────────────┘    │
│                             │                                    │
│                             ▼                                    │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ Resonance State Query:                                  │    │
│  │  • Fetch current score & level                          │    │
│  │  • Read decay reason & contributing events              │    │
│  │  • Check recovery conditions                            │    │
│  └─────────────────────────────────────────────────────────┘    │
│                             │                                    │
│                             ▼                                    │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ ThroneLock Resolution (single source of truth):         │    │
│  │  Authority: Neo4j > Neon > Config                       │    │
│  │  If active role exists: may bypass/downgrade LOCKED     │    │
│  └─────────────────────────────────────────────────────────┘    │
│                             │                                    │
│                             ▼                                    │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ Enforcement Decision:                                   │    │
│  │  1. Compute target level from score                     │    │
│  │  2. Check ThroneLock override                           │    │
│  │  3. Look up permitted actions in policy                 │    │
│  │  4. Emit control decision to audit                      │    │
│  └─────────────────────────────────────────────────────────┘    │
│                             │                                    │
│                             ▼                                    │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ Apply Enforcement (if policy permits):                  │    │
│  │  • deny_non_critical → block requests                   │    │
│  │  • require_approval → gate execution                    │    │
│  │  • rate_limit → throttle operations                     │    │
│  │  • hard_block → explicit deny                           │    │
│  └─────────────────────────────────────────────────────────┘    │
│                             │                                    │
│                             ▼                                    │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ Audit Every Decision:                                   │    │
│  │  • CONTROL_PLANE_LEVEL_TRANSITION                       │    │
│  │  • CONTROL_PLANE_RESTRICTED                             │    │
│  │  • CONTROL_PLANE_LOCKED                                 │    │
│  │  • THRONELOCK_ROLE_ENFORCED                             │    │
│  │  • RESONANCE_DECAY_APPLIED                              │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│  ⚠️  HARD RULE: Only policy-permitted actions applied          │
│  ⚠️  HARD RULE: Every enforcement decision audited             │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

---

## Quick Start

### 1. Run Verification (Safe, Read-Only)

```bash
# Test the entire 16A implementation
cd core/ops/scripts

python 16A5_verify_operational_hardening.py

# Output: 5 checks (alerter, enforcer, audit, dry-run safety, recovery)
```

**Expected Output:**
```
✓ CHK_001: Alerter Signal Integrity
✓ CHK_002: Enforcer Policy Application
✓ CHK_003: Audit Trail Completeness
✓ CHK_004: Dry-Run Safety
✓ CHK_005: Recovery & De-escalation

Verification complete: 5/5 checks passed
```

### 2. Run Alerter (Observation Only)

```bash
# Single iteration
python 16A3_telemetry_alerter.py \
  --component system \
  --window 3600 \
  --interval 0 \
  --dry-run

# Continuous (30-second intervals)
python 16A3_telemetry_alerter.py \
  --component agent_execution \
  --interval 30

# Output: Detected anomalies, computed resonance scores
# Writes to: graph_audit_event (telemetry events only)
```

### 3. Run Stabilizer (Policy Enforcement)

```bash
# Single iteration (dry-run by default)
python 16A4_control_plane_stabilizer.py \
  --component agent_execution \
  --component-type agent_execution \
  --interval 0 \
  --dry-run

# Continuous (reads policy, applies enforcement)
python 16A4_control_plane_stabilizer.py \
  --component agent_execution \
  --policy-file enforcement_policy.yaml \
  --thronelock-source neo4j \
  --interval 30

# Output: Control decisions, applied enforcement, audit events
# Writes to: control_plane_resonance_state, graph_audit_event
```

### 4. Query Telemetry (Debug)

```bash
python -c "
from telemetry_query_builder import TelemetryQueryBuilder

builder = TelemetryQueryBuilder()

# Get a specific query
q = builder.query_audit_events_by_type('TELEMETRY_ALERT_RAISED')
print(builder.explain(q))
"
```

---

## Enforcement Levels

| Level | Score Range | Permitted Actions | Use Case |
|-------|-------------|-------------------|----------|
| **INFO** | < 0.2 | (none) | Normal operation; monitoring active |
| **WARN** | 0.2–0.5 | (none; alerter only) | Single anomaly detected; no enforcement |
| **ELEVATED** | 0.5–1.5 | require_approval, audit_all | Pattern emerging; increased scrutiny |
| **RESTRICTED** | 1.5–3.0 | deny_non_critical, rate_limit | Boundaries tightened; only critical allowed |
| **LOCKED** | ≥ 3.0 | hard_block, require_override | Cascading failures; explicit stop |

**De-escalation Automatically Relaxes:**
- LOCKED → RESTRICTED when score drops below 1.5
- RESTRICTED → ELEVATED when score drops below 0.5
- etc.

---

## Resonance Score Computation

```python
resonance_score = Σ(event_weight × decay_factor(age)) / window_length

where:
  event_weight ∈ {
    0.1 (INFO),
    0.5 (WARN),
    1.0 (ELEVATED),
    2.0 (RESTRICTED),
    5.0 (LOCKED)
  }
  
  decay_factor(age) = exp(-age_seconds / half_life_seconds)
  
  window_length = 3600 seconds (default, configurable)
  half_life = 600 seconds (events lose 50% weight after 10 min)
```

**Example:**
- 10 WARN events (weight 0.5) detected 5 minutes ago
- Decay: exp(-300 / 600) ≈ 0.606
- Contribution: 10 × 0.5 × 0.606 ≈ 3.03
- Total score: 3.03 / 100 = 0.0303 → Level: INFO (still monitoring)

---

## ThroneLock Authority Resolution

**Precedence (hard rule):**
1. **Neo4j** (authoritative): Active `graph_role` with valid timestamp
2. **Neon** (fallback): Read replica if Neo4j unavailable
3. **Config** (emergency): Bootstrap/manual override only

**Resolution:**
```python
# Pseudo-code
if neo4j_available:
    roles = query_neo4j("MATCH (r:graph_role {is_active: TRUE}) ...")
else if neon_available:
    roles = query_neon_replica("SELECT * FROM graph_role WHERE is_active ...")
    warn("Neo4j unavailable; using stale Neon replica")
else:
    roles = load_config_file("enforcement_policy.yaml")
    warn("Using emergency config override")
```

---

## Dry-Run Mode (Critical for Testing)

Both alerter and stabilizer support `--dry-run`:

```bash
# Alerter dry-run: compute signals, emit ZERO writes
python 16A3_telemetry_alerter.py --dry-run --interval 0

# Stabilizer dry-run: compute enforcement, apply ZERO changes
python 16A4_control_plane_stabilizer.py --dry-run --interval 0
```

**In Dry-Run:**
- All queries execute
- All anomaly detection runs
- All policy decisions computed
- **But:** No events written to `graph_audit_event`
- **And:** No enforcement actions applied
- **Output:** What WOULD happen

**Verification checks dry-run safety:**
```bash
# Verifier runs both in dry-run and confirms zero changes
python 16A5_verify_operational_hardening.py --dry-run

# Check CHK_004: Dry-Run Safety ensures:
#   - Alerter dry-run makes zero writes
#   - Stabilizer dry-run makes zero enforcement
#   - Both report intended actions
```

---

## Audit Events

All enforcement decisions are logged to `graph_audit_event`:

```sql
SELECT 
  event_type,
  component_id,
  source_level,
  target_level,
  event_data,
  created_at,
  created_by_component
FROM graph_audit_event
WHERE created_by_component IN ('16A3_telemetry_alerter', '16A4_control_plane_stabilizer')
ORDER BY created_at DESC;
```

**Event Types:**
- `TELEMETRY_ALERT_RAISED` — Anomaly detected (alerter)
- `ANOMALY_SPIKE` — Sudden spike detected
- `ANOMALY_TREND` — Sustained pattern detected
- `RESONANCE_SCORE_UPDATED` — Score recalculated
- `CONTROL_PLANE_LEVEL_TRANSITION` — Level changed (stabilizer)
- `CONTROL_PLANE_RESTRICTED` — Enforcement applied
- `CONTROL_PLANE_LOCKED` — Hard block applied
- `THRONELOCK_ROLE_ENFORCED` — ThroneLock override active
- `RESONANCE_DECAY_APPLIED` — Decay/relaxation triggered

---

## Configuration & Tuning

### Environment Variables (Override YAML)

```bash
# Resonance tuning
export RESONANCE_WINDOW_SECONDS=3600
export RESONANCE_HALF_LIFE_SECONDS=600
export RESONANCE_THRESHOLD_WARN=0.2
export RESONANCE_THRESHOLD_ELEVATED=0.5
export RESONANCE_THRESHOLD_RESTRICTED=1.5
export RESONANCE_THRESHOLD_LOCKED=3.0

# Enforcement control
export ENFORCEMENT_ENABLED=true
export ENFORCEMENT_DRY_RUN=false

# ThroneLock authority
export THRONELOCK_SOURCE=neo4j

# Alerting intervals
export ALERTER_INTERVAL_SECONDS=30
```

### Policy File (YAML)

See **[enforcement_policy.yaml](config/enforcement_policy.yaml)** for full structure.

Key sections:
- `policies.<component_type>.<level>.actions` — Permitted enforcement actions
- `thresholds` — Resonance score boundaries
- `thronelock` — Authority source & override behavior
- `audit` — Event types to track

---

## Running in Production

### 1. Start with Dry-Run

```bash
# Week 1: Observe, validate no interference
python 16A3_telemetry_alerter.py --interval 30 &
python 16A4_control_plane_stabilizer.py --dry-run --interval 30 &

# Monitor output; verify decisions are sensible
# Check graph_audit_event for alerter events
tail -f logs/alerter.log | grep "ANOMALY\|RESONANCE"
```

### 2. Enable Enforcement Gradually

```bash
# Week 2: Enable enforcer at low threshold
export RESONANCE_THRESHOLD_RESTRICTED=10.0  # Very high, hard to reach

python 16A4_control_plane_stabilizer.py \
  --component agent_execution \
  --enforcement-enabled \
  --interval 30 &

# Monitor for false positives
grep "CONTROL_PLANE_RESTRICTED" logs/enforcer.log
```

### 3. Lower Thresholds Over Time

```bash
# Week 3: Threshold 5.0
# Week 4: Threshold 3.0 (normal)
```

### 4. Monitor & Alert

```bash
# Create dashboards from graph_audit_event
SELECT 
  DATE_TRUNC('minute', created_at) as minute,
  event_type,
  COUNT(*) as count
FROM graph_audit_event
WHERE created_by_component IN ('16A3_telemetry_alerter', '16A4_control_plane_stabilizer')
  AND created_at > NOW() - INTERVAL '1 hour'
GROUP BY minute, event_type
ORDER BY minute DESC;
```

---

## Troubleshooting

### Problem: Alerter producing too many events

**Causes:**
- Threshold too low
- Data quality issue (spiky metrics)
- Legitimate high activity

**Fix:**
```bash
# Increase resonance thresholds
export RESONANCE_THRESHOLD_WARN=0.5  # was 0.2
export RESONANCE_THRESHOLD_ELEVATED=1.5  # was 0.5

# Or increase half-life (events decay slower)
export RESONANCE_HALF_LIFE_SECONDS=1200  # was 600
```

### Problem: Stabilizer stuck at LOCKED level

**Cause:** Recovery conditions not clearing

**Fix:**
```bash
# Check contributing events
SELECT contributing_events, decay_reason, last_computed
FROM control_plane_resonance_state
WHERE component_id = 'your_component'
AND level = 'LOCKED';

# Manual reset (if warranted)
# Insert audit event with reason, then reset state:
DELETE FROM control_plane_resonance_state
WHERE component_id = 'your_component';

# Stabilizer will recompute on next iteration
```

### Problem: ThroneLock not working

**Cause:** Wrong authority source or stale data

**Fix:**
```bash
# Verify Neo4j query
cypher-shell "MATCH (r:graph_role {is_active: TRUE}) RETURN r LIMIT 10"

# If Neo4j unavailable, check Neon fallback
psql -d neon_db -c "SELECT * FROM graph_role WHERE is_active = TRUE LIMIT 10;"

# If both unavailable, check config
grep -A 5 "thronelock:" enforcement_policy.yaml
```

---

## Success Criteria for Phase 16A

- [x] Spec defined and locked with enforcement levels
- [x] Alerter computes signals, emits zero enforcement
- [x] Stabilizer applies policy-driven enforcement only
- [x] Resonance decay is rolling-window, recoverable, debuggable
- [x] ThroneLock uses single source of truth
- [x] Dry-run mode works on both alerter and stabilizer
- [x] All transitions logged with reason
- [x] Verifier passes all 5 checks
- [x] No control-plane state change without audit event
- [x] Recovery/de-escalation tested and working

---

## Hard Rules (Non-Negotiable)

1. **Monitoring may suggest; control-plane enforcement must be explicit, explainable, and auditable.**
2. **Telemetry layer (16A3) makes zero state changes.**
3. **Control layer (16A4) applies only policy-permitted actions.**
4. **Every enforcement decision is audited.**
5. **Resonance decay is rolling-window with automatic relaxation.**
6. **ThroneLock resolves from single source of truth.**
7. **Dry-run mode changes nothing.**

---

## Next Phase (16B)

Once Phase 16A is stable:
- Wire operational hardening to live runtime surfaces (agents, decision engine, MoScripts)
- Integrate ThroneLock role-based access into execution paths
- Add recovery automation (automatic rollback, fallback routing)
- Implement advanced patterns (caching, prefetching, prioritization)

---

## References

- **[16A1_OPERATIONAL_HARDENING_SPEC.md](architecture/16A1_OPERATIONAL_HARDENING_SPEC.md)** — Full technical specification
- **[enforcement_policy.yaml](config/enforcement_policy.yaml)** — Policy template
- **Module docs:** Each `16AX_*.py` file has inline docstrings

---

**Status:** Phase 16A locked and ready for runtime integration.
