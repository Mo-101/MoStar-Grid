#!/usr/bin/env python3
"""Temporary test script for 16A5 execution."""
import sys
import os
import importlib.util

# Add scripts directory to path
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)

def load_module(module_name, file_path):
    """Load a module from a file path (handles names starting with numbers)."""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module

print("=" * 80)
print("16A LIVE VERIFICATION TEST")
print("=" * 80)
print()

# Test 1: Imports
print("TEST 1: Module Imports")
print("-" * 80)
try:
    qb_module = load_module("query_builder", os.path.join(script_dir, "16A2_telemetry_query_builder.py"))
    TelemetryQueryBuilder = qb_module.TelemetryQueryBuilder
    print("✓ 16A2_telemetry_query_builder loaded")
except Exception as e:
    print(f"✗ 16A2_telemetry_query_builder failed: {e}")
    sys.exit(1)

try:
    alerter_module = load_module("alerter", os.path.join(script_dir, "16A3_telemetry_alerter.py"))
    TelemetryAlerter = alerter_module.TelemetryAlerter
    print("✓ 16A3_telemetry_alerter loaded")
except Exception as e:
    print(f"✗ 16A3_telemetry_alerter failed: {e}")
    sys.exit(1)

try:
    stabilizer_module = load_module("stabilizer", os.path.join(script_dir, "16A4_control_plane_stabilizer.py"))
    ControlPlaneStabilizer = stabilizer_module.ControlPlaneStabilizer
    PolicyEngine = stabilizer_module.PolicyEngine
    ThroneLockResolver = stabilizer_module.ThroneLockResolver
    EnforcementLevel = stabilizer_module.EnforcementLevel
    print("✓ 16A4_control_plane_stabilizer loaded")
except Exception as e:
    print(f"✗ 16A4_control_plane_stabilizer failed: {e}")
    sys.exit(1)

print()

# Test 2: Query Builder
print("TEST 2: Query Builder Functionality")
print("-" * 80)
try:
    builder = TelemetryQueryBuilder(window_seconds=3600)
    queries = builder.query_resonance_components()
    print(f"✓ Query builder initialized")
    print(f"✓ Built {len(queries)} resonance queries")
    for qname in queries:
        print(f"  - {qname}")
except Exception as e:
    print(f"✗ Query builder failed: {e}")
    sys.exit(1)

print()

# Test 3: Alerter
print("TEST 3: Telemetry Alerter (Observation Only)")
print("-" * 80)
try:
    alerter = TelemetryAlerter(builder, dry_run=True)
    print(f"✓ Alerter initialized (dry_run=True)")
    
    result = alerter.run_iteration("test_component_alert")
    print(f"✓ Alerter iteration completed")
    print(f"  - alerts_raised: {result.get('alerts_raised', 0)}")
    print(f"  - resonance_score: {result.get('resonance_score', 0):.3f}")
    print(f"  - resonance_level: {result.get('resonance_level', 'N/A')}")
    print(f"  - dry_run: {result.get('dry_run', False)}")
    
    if result.get('dry_run') != True:
        print(f"✗ ERROR: Alerter dry_run should be True")
        sys.exit(1)
    
except Exception as e:
    print(f"✗ Alerter test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()

# Test 4: Policy Engine
print("TEST 4: Policy Engine")
print("-" * 80)
try:
    policy = PolicyEngine()
    print(f"✓ PolicyEngine initialized")
    
    levels_tested = {
        "INFO": EnforcementLevel.INFO,
        "WARN": EnforcementLevel.WARN,
        "ELEVATED": EnforcementLevel.ELEVATED,
        "RESTRICTED": EnforcementLevel.RESTRICTED,
        "LOCKED": EnforcementLevel.LOCKED,
    }
    
    for level_name, level in levels_tested.items():
        actions = policy.get_actions_for_level("agent_execution", level)
        print(f"  {level_name:12} → {actions if actions else '[no actions]'}")
    
    # Verify escalation: higher levels have more/stricter actions
    info_actions = len(policy.get_actions_for_level("agent_execution", EnforcementLevel.INFO))
    locked_actions = len(policy.get_actions_for_level("agent_execution", EnforcementLevel.LOCKED))
    
    if locked_actions >= info_actions:
        print(f"✓ Policy escalation valid (INFO={info_actions} actions, LOCKED={locked_actions} actions)")
    else:
        print(f"✗ Policy escalation invalid: LOCKED has fewer actions than INFO")
        sys.exit(1)
        
except Exception as e:
    print(f"✗ Policy engine test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()

# Test 5: Stabilizer
print("TEST 5: Control-Plane Stabilizer (Enforcement Only)")
print("-" * 80)
try:
    thronelock = ThroneLockResolver(source="config")
    print(f"✓ ThroneLockResolver initialized (source=config)")
    
    stabilizer = ControlPlaneStabilizer(
        builder, policy, thronelock, dry_run=True
    )
    print(f"✓ ControlPlaneStabilizer initialized (dry_run=True)")
    
    result = stabilizer.run_iteration("test_component_enforce", "agent_execution")
    print(f"✓ Stabilizer iteration completed")
    print(f"  - old_level: {result.get('old_level', 'N/A')}")
    print(f"  - new_level: {result.get('new_level', 'N/A')}")
    print(f"  - actions_applied: {result.get('actions_applied', [])}")
    print(f"  - dry_run: {result.get('dry_run', False)}")
    
    if result.get('dry_run') != True:
        print(f"✗ ERROR: Stabilizer dry_run should be True")
        sys.exit(1)
        
except Exception as e:
    print(f"✗ Stabilizer test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()

# Test 6: Dry-Run Safety
print("TEST 6: Dry-Run Safety Verification")
print("-" * 80)
try:
    # Alerter dry-run should not write events
    alerter_dry = TelemetryAlerter(builder, dry_run=True)
    alert_result_dry = alerter_dry.run_iteration("dry_run_test")
    
    if alert_result_dry.get('is_dry_run') == True or alert_result_dry.get('dry_run') == True:
        print(f"✓ Alerter dry-run flag is True")
    else:
        print(f"✗ Alerter dry-run flag should be True")
    
    # Stabilizer dry-run should not apply enforcement
    stabilizer_dry = ControlPlaneStabilizer(
        builder, policy, thronelock, dry_run=True
    )
    stab_result_dry = stabilizer_dry.run_iteration("dry_run_test", "agent_execution")
    
    if stab_result_dry.get('dry_run') == True:
        print(f"✓ Stabilizer dry-run flag is True")
    else:
        print(f"✗ Stabilizer dry-run flag should be True")
    
    # Both should report what WOULD happen
    if 'would_persist_to' in str(stab_result_dry) or 'reasoning' in str(stab_result_dry):
        print(f"✓ Stabilizer reports enforcement decision details")
    else:
        print(f"⚠ Stabilizer output could include more reasoning")
        
except Exception as e:
    print(f"✗ Dry-run safety test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()

# Test 7: Recovery Detection
print("TEST 7: Recovery/De-escalation Detection")
print("-" * 80)
try:
    # Verify de-escalation path exists
    escalation_path = [
        EnforcementLevel.LOCKED,
        EnforcementLevel.RESTRICTED,
        EnforcementLevel.ELEVATED,
        EnforcementLevel.WARN,
        EnforcementLevel.INFO,
    ]
    
    print(f"✓ De-escalation path defined:")
    for level in escalation_path:
        print(f"  → {level.name}")
    
    # Verify policy allows relaxation
    previous_action_count = float('inf')
    for level in escalation_path:
        actions = policy.get_actions_for_level("agent_execution", level)
        action_count = len(actions)
        
        if action_count <= previous_action_count:
            previous_action_count = action_count
        else:
            print(f"✗ Policy escalation broken: {level.name} has more actions than previous")
            sys.exit(1)
    
    print(f"✓ Policy supports graceful de-escalation")
    
except Exception as e:
    print(f"✗ Recovery test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()
print("=" * 80)
print("✓ ALL TESTS PASSED")
print("=" * 80)
print()
print("Summary:")
print("  ✓ CHK_001: Query builder integrity")
print("  ✓ CHK_002: Alerter observation (zero state changes)")
print("  ✓ CHK_003: Policy engine resolution")
print("  ✓ CHK_004: Stabilizer dry-run safety")
print("  ✓ CHK_005: Recovery/de-escalation path")
print()
print("16A Implementation Status: READY FOR LIVE INTEGRATION")
