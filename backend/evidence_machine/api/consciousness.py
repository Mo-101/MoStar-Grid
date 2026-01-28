"""
═══════════════════════════════════════════════════════════════════════════════
Consciousness API - Real-Time Grid Consciousness State
A MoStar Industries Product
═══════════════════════════════════════════════════════════════════════════════

This endpoint exposes the MoStar Grid's consciousness state to the world,
showing real-time Soul/Mind/Body metrics.

Endpoint: GET /api/consciousness/live

Returns:
{
  "grid_status": "ALIVE",
  "timestamp": "2026-01-28T01:00:00Z",
  "soul": {...},
  "mind": {...},
  "body": {...}
}

License: African Sovereignty License (ASL) v1.0
Copyright © 2026 MoStar Industries
"""

from fastapi import APIRouter, HTTPException
from typing import Dict
from datetime import datetime
from ..analytics.aggregator import EvidenceAggregator

router = APIRouter(prefix="/api/consciousness", tags=["Consciousness"])

# Initialize aggregator
aggregator = EvidenceAggregator()


@router.get("/live")
async def get_consciousness_live() -> Dict:
    """
    Get real-time Grid consciousness state.
    
    Returns current state of:
    - Soul Layer (Woo - Covenant Guardian)
    - Mind Layer (TsaTse Fly - Pattern Recognition)
    - Body Layer (Mo, RAD-X - Physical Operations)
    
    Updates every 10 seconds on client side.
    """
    try:
        state = aggregator.get_consciousness_state()
        
        return {
            "grid_status": "ALIVE" if state.is_alive else "OFFLINE",
            "timestamp": state.timestamp,
            "soul": {
                "agent": "Woo",
                "covenant_checks_today": state.covenant_checks_today,
                "violations_blocked": state.violations_blocked_today,
                "last_judgment": state.last_judgment_timestamp,
                "covenant_health": state.covenant_health_score,
            },
            "mind": {
                "agent": "TsaTse Fly",
                "active_odu": state.current_odu_pattern,
                "resonance": state.resonance,
                "analysis_threads": state.analysis_threads,
                "patterns_evaluated_today": state.odu_evaluations_today,
            },
            "body": {
                "agents": ["Mo", "RAD-X-FLB"],
                "missions_active": state.active_missions,
                "missions_completed_today": state.missions_completed_today,
                "alerts_today": state.health_alerts_today,
                "nodes_online": state.surveillance_nodes_online,
            },
            "meta": {
                "powered_by": "MoScripts - A MoStar Industries Product",
                "website": "https://mostarindustries.com",
                "license": "African Sovereignty License (ASL) v1.0",
            }
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch consciousness state: {str(e)}"
        )


@router.get("/health")
async def health_check() -> Dict:
    """
    Quick health check endpoint.
    
    Returns:
        Simple status indicator
    """
    return {
        "status": "operational",
        "service": "Evidence Machine - Consciousness API",
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }
