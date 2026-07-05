#!/usr/bin/env python3
"""
16A Live Verification - Direct Execution

Runs Phase 16A verifier with actual module loading.
"""

import os
import sys
import importlib.util

# Setup
script_dir = os.path.dirname(os.path.abspath(__file__))

def load_module(code, name):
    """Load module by file path."""
    spec = importlib.util.spec_from_file_location(
        code,
        os.path.join(script_dir, f"{code}_{name}.py")
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[code] = module
    spec.loader.exec_module(module)
    return module

# Load all modules
print("Loading modules...")
try:
    m16a2 = load_module("16A2", "telemetry_query_builder")
    m16a3 = load_module("16A3", "telemetry_alerter")
    m16a4 = load_module("16A4", "control_plane_stabilizer")
    m16a5 = load_module("16A5", "verify_operational_hardening")
    print("✓ All modules loaded successfully\n")
except Exception as e:
    print(f"✗ Module loading failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Run verifier
print("=" * 80)
print("PHASE 16A: OPERATIONAL HARDENING VERIFICATION")
print("=" * 80)
print()

try:
    verifier_class = m16a5.OperationalHardeningVerifier
    verifier = verifier_class(dry_run_mode=True)
    results = verifier.run_all_checks()
    
    print()
    print("=" * 80)
    print("VERIFICATION RESULTS")
    print("=" * 80)
    
    # Parse results
    if isinstance(results, dict):
        checks_passed = results.get("checks_passed", 0)
        checks_total = results.get("checks_total", 0)
        overall = results.get("overall_passed", False)
        
        print(f"\nTotal: {checks_passed}/{checks_total} checks passed")
        print(f"Status: {'✓ PASS' if overall else '✗ FAIL'}\n")
        
        # Detailed results
        for result in results.get("results", []):
            status = "✓" if result.get("passed") else "✗"
            print(f"{status} {result.get('check_id')}: {result.get('check_name')}")
            if result.get("errors"):
                for err in result.get("errors"):
                    print(f"    ERROR: {err}")
            if result.get("warnings"):
                for warn in result.get("warnings"):
                    print(f"    WARN: {warn}")
        
        print()
        if overall:
            print("✓ PHASE 16A VERIFICATION PASSED")
            print()
            print("Status Summary:")
            print("  ✓ CHK_001: Alerter Signal Integrity")
            print("  ✓ CHK_002: Enforcer Policy Application")
            print("  ✓ CHK_003: Audit Trail Completeness")
            print("  ✓ CHK_004: Dry-Run Safety")
            print("  ✓ CHK_005: Recovery & De-escalation")
            print()
            print("16A is ready for runtime integration.")
            sys.exit(0)
        else:
            print("✗ PHASE 16A VERIFICATION FAILED")
            sys.exit(1)
            
except Exception as e:
    print(f"\n✗ Verifier execution failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
