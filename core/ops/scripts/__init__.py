"""
Phase 16A Operational Hardening Package

This __init__.py provides compatibility for importing modules that have
numeric prefixes (16A2, 16A3, 16A4) which are not valid Python module names.
"""

import os
import sys
import importlib.util

_script_dir = os.path.dirname(os.path.abspath(__file__))

def _load_16a_module(module_code: str, module_name: str):
    """Dynamically load a 16A module with numeric prefix."""
    file_path = os.path.join(_script_dir, f"{module_code}_{module_name}.py")
    spec = importlib.util.spec_from_file_location(module_code, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_code] = module
    spec.loader.exec_module(module)
    return module

# Load 16A2: Telemetry Query Builder
try:
    _16A2 = _load_16a_module("16A2", "telemetry_query_builder")
    TelemetryQueryBuilder = _16A2.TelemetryQueryBuilder
    EventSeverity = _16A2.EventSeverity
    MetricSource = _16A2.MetricSource
    TelemetryQuery = _16A2.TelemetryQuery
except Exception as e:
    raise ImportError(f"Failed to load 16A2: {e}")

# Load 16A3: Telemetry Alerter
try:
    _16A3 = _load_16a_module("16A3", "telemetry_alerter")
    TelemetryAlerter = _16A3.TelemetryAlerter
    TelemetryEvent = _16A3.TelemetryEvent
except Exception as e:
    raise ImportError(f"Failed to load 16A3: {e}")

# Load 16A4: Control Plane Stabilizer
try:
    _16A4 = _load_16a_module("16A4", "control_plane_stabilizer")
    ControlPlaneStabilizer = _16A4.ControlPlaneStabilizer
    PolicyEngine = _16A4.PolicyEngine
    ThroneLockResolver = _16A4.ThroneLockResolver
    EnforcementLevel = _16A4.EnforcementLevel
    ControlDecision = _16A4.ControlDecision
except Exception as e:
    raise ImportError(f"Failed to load 16A4: {e}")

__all__ = [
    "TelemetryQueryBuilder",
    "EventSeverity",
    "MetricSource",
    "TelemetryQuery",
    "TelemetryAlerter",
    "TelemetryEvent",
    "ControlPlaneStabilizer",
    "PolicyEngine",
    "ThroneLockResolver",
    "EnforcementLevel",
    "ControlDecision",
]
