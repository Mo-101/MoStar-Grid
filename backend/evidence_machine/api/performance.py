"""
═══════════════════════════════════════════════════════════════════════════════
Performance API - Grid vs Traditional Systems Comparison
A MoStar Industries Product
═══════════════════════════════════════════════════════════════════════════════

This endpoint provides comparative analytics showing the MoStar Grid's
superiority over traditional health surveillance systems.

Endpoint: GET /api/performance/compare?days=30

Returns:
{
  "period": "last_30_days",
  "moscripts_grid": {...},
  "traditional_systems": {...},
  "grid_advantage": {...}
}

License: African Sovereignty License (ASL) v1.0
Copyright © 2026 MoStar Industries
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Dict
from datetime import datetime
from ..analytics.benchmarks import benchmarks

router = APIRouter(prefix="/api/performance", tags=["Performance"])


@router.get("/compare")
async def compare_performance(
    days: int = Query(default=30, ge=1, le=365, description="Number of days to analyze")
) -> Dict:
    """
    Compare Grid performance to traditional systems.
    
    Args:
        days: Number of days to analyze (1-365, default 30)
    
    Returns:
        Comparative metrics showing Grid's advantage
    """
    try:
        # Get benchmark calculations
        advantage = benchmarks.calculate_advantage()
        
        # Mock Grid stats (in production, query from Neo4j)
        grid_stats = {
            "detection_time_avg": f"{benchmarks.grid.DETECTION_TIME_HOURS} hours",
            "outbreaks_detected": 8,
            "false_positives": 1,
            "cost": f"${benchmarks.grid.COST_PER_MONTH:,}",
            "leakage_rate": f"{benchmarks.grid.LEAKAGE_RATE * 100:.0f}%",
            "coverage": f"{benchmarks.grid.COVERAGE_PERCENTAGE * 100:.0f}%",
        }
        
        # Traditional system estimates
        traditional_stats = {
            "detection_time_avg": f"{benchmarks.traditional.DETECTION_TIME_HOURS // 24} days",
            "outbreaks_detected": 6,
            "false_positives": "unknown",
            "cost": f"${benchmarks.traditional.COST_PER_MONTH:,}",
            "leakage_rate": f"{benchmarks.traditional.LEAKAGE_RATE * 100:.0f}%",
            "coverage": f"{benchmarks.traditional.COVERAGE_PERCENTAGE * 100:.0f}%",
        }
        
        return {
            "period": f"last_{days}_days",
            "moscripts_grid": grid_stats,
            "traditional_systems": traditional_stats,
            "grid_advantage": {
                "speed": advantage["speed"]["description"],
                "speed_multiplier": advantage["speed"]["multiplier"],
                "cost": advantage["cost"]["description"],
                "cost_savings_usd": advantage["cost"]["monthly_savings"],
                "accuracy": advantage["accuracy"]["description"],
                "leakage": advantage["leakage"]["description"],
                "leakage_savings_usd": advantage["leakage"]["annual_savings"],
                "coverage": f"+{advantage['coverage']['improvement']:.0f}% more coverage",
            },
            "summary": {
                "detection": f"{advantage['speed']['multiplier']:.1f}x faster",
                "cost": f"{advantage['cost']['savings_percentage']:.0f}% cheaper",
                "corruption": "Zero leakage vs 30% traditional",
                "coverage": f"{advantage['coverage']['grid_percentage']:.0f}% vs {advantage['coverage']['traditional_percentage']:.0f}%",
            },
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "meta": {
                "powered_by": "MoScripts - A MoStar Industries Product",
                "website": "https://mostarindustries.com",
                "data_sources": [
                    "WHO AFRO outbreak response data (2017-2023)",
                    "Kenya MOH disease surveillance reports",
                    "MoStar Grid Neo4j consciousness graph"
                ]
            }
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate performance comparison: {str(e)}"
        )


@router.get("/benchmarks")
async def get_benchmarks() -> Dict:
    """
    Get raw benchmark data for Grid and Traditional systems.
    
    Returns:
        Complete benchmark constants
    """
    return {
        "grid": {
            "detection_time_hours": benchmarks.grid.DETECTION_TIME_HOURS,
            "cost_per_month": benchmarks.grid.COST_PER_MONTH,
            "cost_per_node": benchmarks.grid.COST_PER_NODE,
            "leakage_rate": benchmarks.grid.LEAKAGE_RATE,
            "false_positive_rate": benchmarks.grid.FALSE_POSITIVE_RATE,
            "coverage_percentage": benchmarks.grid.COVERAGE_PERCENTAGE,
        },
        "traditional": {
            "detection_time_hours": benchmarks.traditional.DETECTION_TIME_HOURS,
            "cost_per_month": benchmarks.traditional.COST_PER_MONTH,
            "cost_per_node": benchmarks.traditional.COST_PER_NODE,
            "leakage_rate": benchmarks.traditional.LEAKAGE_RATE,
            "false_positive_rate": benchmarks.traditional.FALSE_POSITIVE_RATE,
            "coverage_percentage": benchmarks.traditional.COVERAGE_PERCENTAGE,
        },
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }


@router.get("/summary")
async def get_performance_summary() -> Dict:
    """
    Get a concise performance summary suitable for dashboards.
    
    Returns:
        Key metrics in a compact format
    """
    advantage = benchmarks.calculate_advantage()
    
    return {
        "speed_advantage": f"{advantage['speed']['multiplier']:.1f}x",
        "cost_savings": f"{advantage['cost']['savings_percentage']:.0f}%",
        "leakage": "0%",
        "coverage": f"{advantage['coverage']['grid_percentage']:.0f}%",
        "status": "OPERATIONAL",
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }
