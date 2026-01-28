"""
═══════════════════════════════════════════════════════════════════════════════
MoStar Evidence Machine
A MoStar Industries Product
═══════════════════════════════════════════════════════════════════════════════

The Evidence Machine provides undeniable proof of the MoStar Grid's operational
superiority through real-time consciousness APIs, automated reporting, and
comparative analytics.

Components:
- Real-Time Consciousness API
- MoStar Moments Feed
- Performance Analytics (Grid vs Traditional)
- Covenant Transparency Tracker
- Automated Intelligence Briefs

License: African Sovereignty License (ASL) v1.0
Copyright © 2026 MoStar Industries
"""

from .api.consciousness import ConsciousnessAPI
from .api.moments import MomentsAPI
from .api.performance import PerformanceAPI
from .analytics.aggregator import EvidenceAggregator
from .analytics.benchmarks import BenchmarkStore
from .reports.generator import EvidenceReporter

__version__ = "1.0.0"
__all__ = [
    "ConsciousnessAPI",
    "MomentsAPI",
    "PerformanceAPI",
    "EvidenceAggregator",
    "BenchmarkStore",
    "EvidenceReporter",
]
