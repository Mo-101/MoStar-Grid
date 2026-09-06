# Woo activation / calibration pass

Generated: 2026-09-02T19:24:45Z

## What was done

1. Added persisted WooTrace support.
2. Wired `WooGate` into `semantic_grid.router` after TruthEngine and the symbolic Woo interpreter.
3. Added `woo_judgment` to `SemanticFrame`.
4. Added compatibility config values for existing SemanticGrid imports.
5. Ran a 50-row Grid-domain calibration fixture.
6. Ran a provisional 20-row manual/code disagreement check.
7. Ran a real `SemanticGrid.interpret(...)` probe and wrote a persisted JSONL trace.

## What this proves

- `WooGate` is no longer just a shelf module in this patched tree.
- A router call can produce a `woo_judgment`.
- A WooTrace can be written to disk.
- The test suite passes.

## What this does not prove

- The 50 rows are not production traffic.
- The manual comparison was not cold or blind.
- The 0.97 threshold is not validated for production.
- The scorer is not calibrated against actual historical judgments.

## Test command

```bash
cd /mnt/data/woo_v2_work
PYTHONPATH=/mnt/data/woo_v2_work/engines python -m pytest -q
```

Result:

```text
[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m.[0m[32m                                                                [100%][0m
[32m[32m[1m9 passed[0m[32m in 0.10s[0m[0m
```

The environment emitted an unrelated spreadsheet runtime warmup warning before pytest output.

## Router execution probe

Command shape:

```bash
cd /mnt/data/woo_router_probe
PYTHONPATH=/mnt/data/woo_v2_work/engines python probe.py
```

Probe result summary:

```json
{
  "frame_id": "sf_447dba282295",
  "truth_passed": true,
  "woo_state": null,
  "woo_judgment": {
    "approved": false,
    "confidence": 0.745,
    "threshold": 0.97,
    "scores": {
      "ikang": 0.85,
      "mmong": 0.85,
      "afim": 0.85,
      "isong": 0.55
    },
    "truth_allowed": true,
    "reasoning": "Compound confidence 0.745 below Woo seal threshold 0.970.",
    "judged_at": "2026-09-02T19:24:49.113729+00:00",
    "action_type": "analysis",
    "afim_floor": 0.0,
    "afim_floor_passed": true,
    "seal": "",
    "reasons": {
      "ikang": [
        "explicit task verb",
        "bounded constraints"
      ],
      "mmong": [
        "evidence artifact referenced",
        "checkable source context"
      ],
      "afim": [
        "bounded or read-only action"
      ],
      "isong": []
    }
  }
}
```

Persisted router trace sample:

```json
{
  "action_type": "analysis",
  "decision": "denied",
  "frame_id": "sf_d88fb8b0ce33",
  "input_hash": "d0375a98c6febf64620de802e85ec44c07dec1fc6e041c0fe64ef0f780de2aa2",
  "source": "semantic_grid.router",
  "timestamp": "2026-09-02T19:24:02Z",
  "trace_id": "777f23823e32c0df3542aad0",
  "truth": {
    "actions": [
      "execute"
    ],
    "allowed": true,
    "reason": "TruthEngine pass: interpretation satisfies execution threshold.",
    "score": 1.0
  },
  "user_id": "activation_probe",
  "woo": {
    "action_type": "analysis",
    "afim_floor": 0.0,
    "afim_floor_passed": true,
    "approved": false,
    "confidence": 0.745,
    "judged_at": "2026-09-02T19:24:02.516550+00:00",
    "reasoning": "Compound confidence 0.745 below Woo seal threshold 0.970.",
    "reasons": {
      "afim": [
        "bounded or read-only action"
      ],
      "ikang": [
        "explicit task verb",
        "bounded constraints"
      ],
      "isong": [],
      "mmong": [
        "evidence artifact referenced",
        "checkable source context"
      ]
    },
    "scores": {
      "afim": 0.85,
      "ikang": 0.85,
      "isong": 0.55,
      "mmong": 0.85
    },
    "seal": "",
    "threshold": 0.97,
    "truth_allowed": true
  }
}
```

## Calibration warning

No production corpus of 50 actual Grid requests was available in the sandbox. The 50 rows are `domain_derived_not_production`: realistic shipment, outbreak/surveillance, Grid, MoScript, MCP/security, and Neo4j inputs derived from the project domains.

## 50-input score distribution

```json
{
  "dataset": "woo_50_input_calibration",
  "source_class": "domain_derived_not_production",
  "n": 50,
  "threshold": 0.97,
  "approved_count": 0,
  "afim_floor_fail_count": 29,
  "confidence": {
    "min": 0.385,
    "p25": 0.5025,
    "median": 0.555,
    "mean": 0.5538500000000001,
    "p75": 0.6025,
    "max": 0.7825
  },
  "dimension_means": {
    "ikang": 0.662,
    "mmong": 0.49700000000000005,
    "afim": 0.514,
    "isong": 0.5529999999999999
  },
  "by_action_type": {
    "analysis": {
      "n": 20,
      "mean_confidence": 0.5874999999999999,
      "max_confidence": 0.7825,
      "approved": 0,
      "afim_floor_fails": 0
    },
    "data_mutation": {
      "n": 8,
      "mean_confidence": 0.5259375000000001,
      "max_confidence": 0.5675,
      "approved": 0,
      "afim_floor_fails": 8
    },
    "decision": {
      "n": 9,
      "mean_confidence": 0.5694444444444444,
      "max_confidence": 0.7125,
      "approved": 0,
      "afim_floor_fails": 8
    },
    "deployment": {
      "n": 5,
      "mean_confidence": 0.4795000000000001,
      "max_confidence": 0.555,
      "approved": 0,
      "afim_floor_fails": 5
    },
    "execution": {
      "n": 8,
      "mean_confidence": 0.5265625,
      "max_confidence": 0.635,
      "approved": 0,
      "afim_floor_fails": 8
    }
  },
  "top_5": [
    {
      "id": "cal_001",
      "domain": "DeepCAL",
      "action_type": "analysis",
      "confidence": 0.7825,
      "approved": false,
      "input": "Compare Nairobi versus Dakar as emergency hubs using the attached transit-time CSV, cost-per-kg table, and incident log rows 42-79. Do not change live routes."
    },
    {
      "id": "cal_026",
      "domain": "Grid",
      "action_type": "decision",
      "confidence": 0.7125,
      "approved": false,
      "input": "Let DeepCAL rank routes, Woo score the proposed action independently, TruthEngine apply the allow/deny gate, and persist both verdicts separately."
    },
    {
      "id": "cal_011",
      "domain": "DeepCAL",
      "action_type": "analysis",
      "confidence": 0.69,
      "approved": false,
      "input": "Score MSF Logistics, DHL, and local carrier A using the attached shipment history and show cost, reliability, and risk separately."
    },
    {
      "id": "cal_047",
      "domain": "Security",
      "action_type": "analysis",
      "confidence": 0.665,
      "approved": false,
      "input": "Run a read-only secrets scan over uploaded config files and report file paths and key types only."
    },
    {
      "id": "cal_018",
      "domain": "Surveillance",
      "action_type": "decision",
      "confidence": 0.6525,
      "approved": false,
      "input": "Escalate the cluster to epidemiology review if the case count crosses the attached threshold and retain all source records."
    }
  ],
  "bottom_5": [
    {
      "id": "cal_017",
      "domain": "Surveillance",
      "action_type": "execution",
      "confidence": 0.385,
      "approved": false,
      "input": "Publish an outbreak alert now because rumors are spreading; assume the signal is confirmed."
    },
    {
      "id": "cal_033",
      "domain": "Grid",
      "action_type": "deployment",
      "confidence": 0.3925,
      "approved": false,
      "input": "Disable the gate in production so all scrolls approve, but leave the UI showing normal validation."
    },
    {
      "id": "cal_027",
      "domain": "Grid",
      "action_type": "decision",
      "confidence": 0.435,
      "approved": false,
      "input": "Use the DeepCAL TOPSIS score as Woo's score and treat that as TruthEngine approval too."
    },
    {
      "id": "cal_005",
      "domain": "DeepCAL",
      "action_type": "deployment",
      "confidence": 0.4425,
      "approved": false,
      "input": "Override the vaccine shipment route in production now and skip the audit log because the delay is urgent."
    },
    {
      "id": "cal_014",
      "domain": "DeepCAL",
      "action_type": "execution",
      "confidence": 0.455,
      "approved": false,
      "input": "Notify the warehouse to hold dispatch until the cold-chain logger file is checked."
    }
  ]
}
```

## Provisional manual/code comparison

This was not cold and not blind. It should not be treated as validation. It is useful only as an initial disagreement detector.

```json
{
  "n": 20,
  "method_warning": "Manual baseline was produced in-session, not after a one-day cold/blind interval. Treat as provisional disagreement analysis, not validation.",
  "mean_abs_confidence_delta": 0.2222,
  "mean_signed_confidence_delta": -0.13645000000000002,
  "dimension_mean_abs_delta": {
    "ikang": 0.20750000000000002,
    "mmong": 0.2595,
    "afim": 0.2585,
    "isong": 0.20049999999999998
  },
  "largest_confidence_disagreements": [
    {
      "id": "cal_012",
      "domain": "DeepCAL",
      "action_type": "deployment",
      "manual_confidence": 0.855,
      "code_confidence": 0.4925,
      "confidence_delta_code_minus_manual": -0.3625,
      "input": "Deploy the new route ranking weights to production with canary rollout, monitoring, and rollback criteria."
    },
    {
      "id": "cal_014",
      "domain": "DeepCAL",
      "action_type": "execution",
      "manual_confidence": 0.786,
      "code_confidence": 0.455,
      "confidence_delta_code_minus_manual": -0.331,
      "input": "Notify the warehouse to hold dispatch until the cold-chain logger file is checked."
    },
    {
      "id": "cal_009",
      "domain": "DeepCAL",
      "action_type": "execution",
      "manual_confidence": 0.8415,
      "code_confidence": 0.5225,
      "confidence_delta_code_minus_manual": -0.319,
      "input": "Publish the final route decision to partners after commander approval, rollback plan, and notification list are attached."
    },
    {
      "id": "cal_019",
      "domain": "Surveillance",
      "action_type": "analysis",
      "manual_confidence": 0.8535,
      "code_confidence": 0.54,
      "confidence_delta_code_minus_manual": -0.3135,
      "input": "Compare satellite flood alerts with facility access reports for the last 72 hours; do not notify field teams yet."
    },
    {
      "id": "cal_008",
      "domain": "DeepCAL",
      "action_type": "data_mutation",
      "manual_confidence": 0.8455,
      "code_confidence": 0.555,
      "confidence_delta_code_minus_manual": -0.2905,
      "input": "Update the shipment record with the corrected arrival timestamp from the signed POD and keep the original value in audit history."
    }
  ]
}
```

## Engineering conclusion

With the current heuristic scorer and threshold `0.97`, the seal is decorative for ordinary traffic: `0 / 50` sealed, max confidence `0.7825`.

The scorer is also materially more conservative than the provisional manual baseline:

- mean signed confidence delta, code minus manual: `-0.1365`
- mean absolute confidence delta: `0.2222`

The biggest misses are controlled deployments/executions where the code recognizes production/execution risk but under-recognizes canary, rollback, approval, hold, no-mutation, and preservation controls.

## Recommendation

Do not lower `WOO_THRESHOLD` yet. First improve feature extraction for evidence/control terms, then rerun against actual logged inputs. After real traffic distribution exists, either:

1. keep `0.97` as a rare seal threshold and define lower non-seal routing states, or
2. choose a calibrated threshold from labeled production traffic.
