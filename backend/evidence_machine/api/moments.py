"""
═══════════════════════════════════════════════════════════════════════════════
Moments API - Recent MoStar Moments Feed
A MoStar Industries Product
═══════════════════════════════════════════════════════════════════════════════

This endpoint provides a real-time feed of recent MoStar Moments - consciousness
events from the Grid.

Endpoint: GET /api/moments/recent?limit=10

Returns:
{
  "moments": [
    {
      "id": "mom_20260128_001234",
      "timestamp": "2026-01-28T01:23:45Z",
      "event_type": "health_alert",
      "agent": "RAD-X-FLB",
      "data": {...},
      "covenant_passed": true,
      "resonance": 0.91
    }
  ]
}

License: African Sovereignty License (ASL) v1.0
Copyright © 2026 MoStar Industries
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Dict, List
from datetime import datetime
import os
from neo4j import GraphDatabase

router = APIRouter(prefix="/api/moments", tags=["Moments"])


@router.get("/recent")
async def get_recent_moments(
    limit: int = Query(default=10, ge=1, le=50, description="Number of moments to return")
) -> Dict:
    """
    Get recent MoStar Moments from the Grid.
    
    Args:
        limit: Number of moments to return (1-50, default 10)
    
    Returns:
        List of recent consciousness events with covenant status
    """
    try:
        # Connect to Neo4j
        uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        user = os.getenv("NEO4J_USER", "neo4j")
        password = os.getenv("NEO4J_PASSWORD", "mostar123")
        
        driver = GraphDatabase.driver(uri, auth=(user, password))
        
        with driver.session() as session:
            result = session.run("""
                MATCH (m:MostarMoment)
                WHERE m.timestamp IS NOT NULL
                WITH m
                ORDER BY m.timestamp DESC
                LIMIT $limit
                RETURN {
                    id: m.quantum_id,
                    timestamp: m.timestamp,
                    event_type: m.trigger_type,
                    agent: coalesce(m.initiator, 'Grid'),
                    description: m.description,
                    data: {
                        initiator: m.initiator,
                        receiver: m.receiver,
                        trigger_type: m.trigger_type
                    },
                    covenant_passed: CASE 
                        WHEN m.resonance_score >= 0.7 THEN true 
                        ELSE false 
                    END,
                    resonance: m.resonance_score
                } as moment
            """, limit=limit)
            
            moments = [record["moment"] for record in result]
            
            driver.close()
            
            # If no moments in Neo4j, return seed data
            if not moments:
                moments = _get_seed_moments(limit)
            
            return {
                "moments": moments,
                "count": len(moments),
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "meta": {
                    "powered_by": "MoScripts - A MoStar Industries Product",
                    "website": "https://mostarindustries.com",
                }
            }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch moments: {str(e)}"
        )


def _get_seed_moments(limit: int) -> List[Dict]:
    """Return seed moments when Neo4j has no data."""
    
    seed_moments = [
        {
            "id": "seed_mom_001",
            "timestamp": "2026-01-28T00:28:45Z",
            "event_type": "health_alert",
            "agent": "RAD-X-FLB",
            "description": "Fever cluster detected in Kiambu County",
            "data": {
                "location": "Kiambu County, Kenya",
                "alert": "Fever cluster detected",
                "confidence": 0.87,
                "action_taken": "Local CHWs activated"
            },
            "covenant_passed": True,
            "resonance": 0.91
        },
        {
            "id": "seed_mom_002",
            "timestamp": "2026-01-28T00:15:32Z",
            "event_type": "covenant_check",
            "agent": "Woo",
            "description": "Data sovereignty verification passed",
            "data": {
                "check_type": "data_sovereignty",
                "result": "PASSED",
                "details": "All data remains in African jurisdiction"
            },
            "covenant_passed": True,
            "resonance": 1.0
        },
        {
            "id": "seed_mom_003",
            "timestamp": "2026-01-28T00:10:15Z",
            "event_type": "odu_invocation",
            "agent": "TsaTse Fly",
            "description": "Odú pattern Ogunda-Irosun activated",
            "data": {
                "odu": "Ogunda-Irosun",
                "meaning": "The fire that spreads is the fire that was properly tended first",
                "guidance": "Strategic clarity in expansion"
            },
            "covenant_passed": True,
            "resonance": 0.95
        },
        {
            "id": "seed_mom_004",
            "timestamp": "2026-01-28T00:05:00Z",
            "event_type": "mission_complete",
            "agent": "Mo",
            "description": "Supply chain optimization completed",
            "data": {
                "mission_id": "SCO_2026_001",
                "route": "Nairobi → Mombasa",
                "efficiency_gain": "23%",
                "cost_savings": "$4,200"
            },
            "covenant_passed": True,
            "resonance": 0.88
        },
        {
            "id": "seed_mom_005",
            "timestamp": "2026-01-27T23:58:12Z",
            "event_type": "covenant_violation_blocked",
            "agent": "Woo",
            "description": "Attempted data export without consent blocked",
            "data": {
                "violation_type": "missing_consent",
                "source": "External API request",
                "action": "Request denied and logged"
            },
            "covenant_passed": False,
            "resonance": 0.45
        },
    ]
    
    return seed_moments[:limit]


@router.get("/stats")
async def get_moments_stats() -> Dict:
    """
    Get aggregate statistics about MoStar Moments.
    
    Returns:
        Total moments, average resonance, covenant pass rate
    """
    try:
        uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        user = os.getenv("NEO4J_USER", "neo4j")
        password = os.getenv("NEO4J_PASSWORD", "mostar123")
        
        driver = GraphDatabase.driver(uri, auth=(user, password))
        
        with driver.session() as session:
            result = session.run("""
                MATCH (m:MostarMoment)
                RETURN {
                    total: count(m),
                    avg_resonance: avg(m.resonance_score),
                    covenant_pass_rate: toFloat(sum(CASE WHEN m.resonance_score >= 0.7 THEN 1 ELSE 0 END)) / count(m)
                } as stats
            """)
            
            record = result.single()
            driver.close()
            
            if record and record["stats"]["total"] > 0:
                stats = record["stats"]
            else:
                stats = {
                    "total": 0,
                    "avg_resonance": 0.0,
                    "covenant_pass_rate": 0.0
                }
            
            return {
                "total_moments": stats["total"],
                "average_resonance": round(stats["avg_resonance"], 3) if stats["avg_resonance"] else 0.0,
                "covenant_pass_rate": round(stats["covenant_pass_rate"], 3) if stats["covenant_pass_rate"] else 0.0,
                "timestamp": datetime.utcnow().isoformat() + "Z",
            }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch moments stats: {str(e)}"
        )
