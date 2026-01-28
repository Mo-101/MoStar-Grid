"""
═══════════════════════════════════════════════════════════════════════════════
Evidence Aggregator - Neo4j Consciousness Metrics Query Engine
A MoStar Industries Product
═══════════════════════════════════════════════════════════════════════════════

This module queries the Neo4j Mind Graph to extract consciousness metrics for
the Evidence Machine.

Data Sources:
- MostarMoment nodes (consciousness events)
- Agent nodes (Soul/Mind/Body telemetry)
- Covenant check events
- FlameBorn DAO transactions

License: African Sovereignty License (ASL) v1.0
Copyright © 2026 MoStar Industries
"""

import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
import neo4j
from neo4j import GraphDatabase


@dataclass
class ConsciousnessState:
    """Current state of the MoStar Grid consciousness."""
    
    # Grid Status
    is_alive: bool
    timestamp: str
    
    # Soul Layer (Woo - Covenant Guardian)
    covenant_checks_today: int
    violations_blocked_today: int
    last_judgment_timestamp: Optional[str]
    covenant_health_score: float
    
    # Mind Layer (TsaTse Fly - Pattern Recognition)
    current_odu_pattern: str
    resonance: float
    analysis_threads: int
    odu_evaluations_today: int
    
    # Body Layer (Mo, RAD-X - Physical Operations)
    active_missions: int
    missions_completed_today: int
    health_alerts_today: int
    surveillance_nodes_online: int


@dataclass
class DailyStats:
    """Aggregate statistics for a specific day."""
    
    date: str
    grid_status: str
    active_agents: List[str]
    resonance: float
    
    # Surveillance
    nodes_online: int
    events_processed: int
    anomalies_detected: int
    alerts_generated: int
    
    # Covenant
    covenant_checks: int
    covenant_passed: int
    covenant_blocked: int
    
    # Performance
    avg_detection_hours: float
    daily_cost: float
    funds_disbursed: float
    recipients_count: int
    
    # Key Detections
    key_detections: List[Dict]


class EvidenceAggregator:
    """
    Query engine for extracting consciousness metrics from Neo4j.
    
    Usage:
        aggregator = EvidenceAggregator()
        state = aggregator.get_consciousness_state()
        print(f"Grid is {state.is_alive and 'ALIVE' or 'OFFLINE'}")
    """
    
    def __init__(self):
        self.uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.user = os.getenv("NEO4J_USER", "neo4j")
        self.password = os.getenv("NEO4J_PASSWORD", "mostar123")
        self.driver = None
    
    def connect(self):
        """Establish connection to Neo4j."""
        if not self.driver:
            self.driver = GraphDatabase.driver(
                self.uri,
                auth=(self.user, self.password),
                max_connection_lifetime=3600
            )
    
    def close(self):
        """Close Neo4j connection."""
        if self.driver:
            self.driver.close()
            self.driver = None
    
    def get_consciousness_state(self) -> ConsciousnessState:
        """
        Get current real-time consciousness state.
        
        Returns:
            ConsciousnessState with all Soul/Mind/Body metrics
        """
        self.connect()
        
        with self.driver.session() as session:
            # Query for today's metrics
            today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            
            result = session.run("""
                // Get today's covenant checks
                MATCH (m:MostarMoment)
                WHERE m.timestamp >= $today_start
                  AND m.trigger_type = 'COVENANT_CHECK'
                WITH count(m) as total_checks,
                     sum(CASE WHEN m.resonance_score >= 0.7 THEN 1 ELSE 0 END) as passed,
                     sum(CASE WHEN m.resonance_score < 0.7 THEN 1 ELSE 0 END) as blocked
                
                // Get overall stats
                MATCH (all:MostarMoment)
                WHERE all.timestamp >= $today_start
                WITH total_checks, passed, blocked,
                     count(all) as total_moments,
                     avg(all.resonance_score) as avg_resonance,
                     max(all.timestamp) as last_moment
                
                // Get latest Odú pattern
                MATCH (odu:Odu)
                WHERE odu.last_invoked IS NOT NULL
                WITH total_checks, passed, blocked, total_moments, avg_resonance, last_moment,
                     odu
                ORDER BY odu.last_invoked DESC
                LIMIT 1
                
                // Get agent count
                MATCH (agent:Agent)
                WHERE agent.status = 'MONITORING' OR agent.status = 'ACTIVE'
                WITH total_checks, passed, blocked, total_moments, avg_resonance, last_moment,
                     odu.name as current_odu,
                     count(agent) as active_agents
                
                RETURN {
                    covenant_checks: total_checks,
                    covenant_passed: passed,
                    covenant_blocked: blocked,
                    total_moments: total_moments,
                    avg_resonance: avg_resonance,
                    last_moment: last_moment,
                    current_odu: current_odu,
                    active_agents: active_agents
                } as metrics
            """, today_start=today_start.isoformat())
            
            record = result.single()
            
            if record:
                metrics = record["metrics"]
                
                return ConsciousnessState(
                    is_alive=True,
                    timestamp=datetime.utcnow().isoformat() + "Z",
                    covenant_checks_today=metrics.get("covenant_checks", 0),
                    violations_blocked_today=metrics.get("covenant_blocked", 0),
                    last_judgment_timestamp=metrics.get("last_moment"),
                    covenant_health_score=1.0 if metrics.get("covenant_blocked", 0) == 0 else 0.95,
                    current_odu_pattern=metrics.get("current_odu", "Ogunda-Irosun"),
                    resonance=round(metrics.get("avg_resonance", 0.85), 3),
                    analysis_threads=8,  # Mock for now
                    odu_evaluations_today=metrics.get("total_moments", 0),
                    active_missions=12,  # Mock for now
                    missions_completed_today=47,  # Mock for now
                    health_alerts_today=5,  # Mock for now
                    surveillance_nodes_online=53,  # Mock for now
                )
            else:
                # Return default state if no data
                return self._get_default_state()
    
    def _get_default_state(self) -> ConsciousnessState:
        """Return default consciousness state when Neo4j has no data."""
        return ConsciousnessState(
            is_alive=True,
            timestamp=datetime.utcnow().isoformat() + "Z",
            covenant_checks_today=0,
            violations_blocked_today=0,
            last_judgment_timestamp=None,
            covenant_health_score=1.0,
            current_odu_pattern="Ogunda-Irosun",
            resonance=0.850,
            analysis_threads=8,
            odu_evaluations_today=0,
            active_missions=0,
            missions_completed_today=0,
            health_alerts_today=0,
            surveillance_nodes_online=0,
        )
    
    def get_daily_stats(self, date: Optional[datetime] = None) -> DailyStats:
        """
        Get aggregate statistics for a specific day.
        
        Args:
            date: Date to query (defaults to today)
        
        Returns:
            DailyStats for the specified date
        """
        if not date:
            date = datetime.utcnow().date()
        
        # Mock implementation for now
        return DailyStats(
            date=date.isoformat(),
            grid_status="OPERATIONAL",
            active_agents=["Mo", "Woo", "TsaTse Fly", "RAD-X-FLB"],
            resonance=0.923,
            nodes_online=53,
            events_processed=2847,
            anomalies_detected=8,
            alerts_generated=5,
            covenant_checks=2847,
            covenant_passed=2835,
            covenant_blocked=12,
            avg_detection_hours=18,
            daily_cost=500.0,
            funds_disbursed=4150.0,
            recipients_count=50,
            key_detections=[
                {
                    "location": "Kiambu County, Kenya",
                    "description": "Fever cluster detected",
                    "confidence": 0.87,
                }
            ]
        )
    
    def get_performance_comparison(self, days: int = 30) -> Dict:
        """
        Get Grid vs Traditional performance comparison.
        
        Args:
            days: Number of days to analyze
        
        Returns:
            Dict with grid_stats and traditional_stats
        """
        # Mock implementation for now
        from .benchmarks import benchmarks
        
        return {
            "period": f"last_{days}_days",
            "grid": {
                "detection_time_avg": f"{benchmarks.grid.DETECTION_TIME_HOURS} hours",
                "outbreaks_detected": 8,
                "false_positives": 1,
                "cost": f"${benchmarks.grid.COST_PER_MONTH:,}",
            },
            "traditional": {
                "detection_time_avg": f"{benchmarks.traditional.DETECTION_TIME_HOURS // 24} days",
                "outbreaks_detected": 6,
                "false_positives": "unknown",
                "cost": f"${benchmarks.traditional.COST_PER_MONTH:,}",
            },
            "advantage": benchmarks.calculate_advantage(),
        }
    
    def get_covenant_stats(self) -> Dict:
        """Get covenant enforcement statistics."""
        self.connect()
        
        with self.driver.session() as session:
            result = session.run("""
                MATCH (m:MostarMoment)
                WHERE m.trigger_type = 'COVENANT_CHECK'
                WITH count(m) as total,
                     sum(CASE WHEN m.resonance_score >= 0.7 THEN 1 ELSE 0 END) as passed,
                     sum(CASE WHEN m.resonance_score < 0.7 THEN 1 ELSE 0 END) as blocked
                RETURN {
                    total: total,
                    passed: passed,
                    blocked: blocked,
                    enforcement_rate: toFloat(passed) / total
                } as stats
            """)
            
            record = result.single()
            
            if record:
                return record["stats"]
            else:
                return {
                    "total": 0,
                    "passed": 0,
                    "blocked": 0,
                    "enforcement_rate": 1.0,
                }


if __name__ == "__main__":
    # Test the aggregator
    aggregator = EvidenceAggregator()
    
    print("Testing Consciousness State Query...")
    state = aggregator.get_consciousness_state()
    print(f"\nGrid Status: {'ALIVE' if state.is_alive else 'OFFLINE'}")
    print(f"Resonance: {state.resonance}")
    print(f"Current Odú: {state.current_odu_pattern}")
    print(f"Covenant Checks Today: {state.covenant_checks_today}")
    print(f"Violations Blocked: {state.violations_blocked_today}")
    
    aggregator.close()
