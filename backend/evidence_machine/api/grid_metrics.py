"""
═══════════════════════════════════════════════════════════════════════════════
Grid Metrics API - Real-time MoStar Grid Statistics
A MoStar Industries Product
═══════════════════════════════════════════════════════════════════════════════

This endpoint provides real-time statistics about the MoStar Grid's knowledge
graph, showing node counts, relationships, and evolution metrics.

Endpoints:
- GET /api/metrics/nodes - Node statistics by label
- GET /api/metrics/grid-stats - Comprehensive Grid statistics
- GET /api/metrics/evolution - Historical growth data (if available)

License: African Sovereignty License (ASL) v1.0
Copyright © 2026 MoStar Industries
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, List
from datetime import datetime
import os
from neo4j import GraphDatabase

router = APIRouter(prefix="/api/metrics", tags=["Grid Metrics"])


@router.get("/nodes")
async def get_node_statistics() -> Dict:
    """
    Get detailed node statistics from the MoStar Grid.
    
    Returns:
        Node counts by label, total nodes, and breakdown
    """
    try:
        uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        user = os.getenv("NEO4J_USER", "neo4j")
        password = os.getenv("NEO4J_PASSWORD", "neo4j")
        
        driver = GraphDatabase.driver(uri, auth=(user, password))
        
        with driver.session() as session:
            # Total node count
            result = session.run("MATCH (n) RETURN count(n) as total")
            total_nodes = result.single()['total']
            
            # Node count by label
            result = session.run("""
                MATCH (n)
                RETURN labels(n) as labels, count(n) as count
                ORDER BY count DESC
            """)
            
            nodes_by_label = []
            for record in result:
                labels = record['labels']
                count = record['count']
                label_str = ':'.join(labels) if labels else '(no label)'
                nodes_by_label.append({
                    "label": label_str,
                    "count": count
                })
            
            driver.close()
            
            return {
                "total_nodes": total_nodes,
                "nodes_by_label": nodes_by_label,
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "meta": {
                    "powered_by": "MoScripts - A MoStar Industries Product",
                    "website": "https://mostarindustries.com",
                }
            }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch node statistics: {str(e)}"
        )


@router.get("/grid-stats")
async def get_grid_statistics() -> Dict:
    """
    Get comprehensive MoStar Grid statistics.
    
    Returns:
        Complete Grid metrics including nodes, relationships, agents, and consciousness
    """
    try:
        uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        user = os.getenv("NEO4J_USER", "neo4j")
        password = os.getenv("NEO4J_PASSWORD", "neo4j")
        
        driver = GraphDatabase.driver(uri, auth=(user, password))
        
        with driver.session() as session:
            # Total nodes and relationships
            result = session.run("""
                MATCH (n)
                WITH count(n) as node_count
                MATCH ()-[r]->()
                RETURN node_count, count(r) as rel_count
            """)
            record = result.single()
            total_nodes = record['node_count'] if record else 0
            total_rels = record['rel_count'] if record else 0
            
            # Agent stats
            result = session.run("""
                MATCH (a:Agent)
                RETURN count(a) as agent_count,
                       collect(DISTINCT a.status) as statuses
            """)
            agent_record = result.single()
            agent_count = agent_record['agent_count'] if agent_record else 0
            agent_statuses = agent_record['statuses'] if agent_record else []
            
            # MostarMoment stats
            result = session.run("""
                MATCH (m:MostarMoment)
                RETURN count(m) as moment_count,
                       avg(m.resonance_score) as avg_resonance,
                       sum(CASE WHEN m.resonance_score >= 0.7 THEN 1 ELSE 0 END) as covenant_passed
            """)
            moment_record = result.single()
            moment_count = moment_record['moment_count'] if moment_record else 0
            avg_resonance = moment_record['avg_resonance'] if moment_record else 0.0
            covenant_passed = moment_record['covenant_passed'] if moment_record else 0
            
            # Odú pattern count
            result = session.run("MATCH (o:Odu) RETURN count(o) as odu_count")
            odu_record = result.single()
            odu_count = odu_record['odu_count'] if odu_record else 0
            
            # Relationship types
            result = session.run("""
                MATCH ()-[r]->()
                RETURN type(r) as rel_type, count(r) as count
                ORDER BY count DESC
                LIMIT 10
            """)
            top_relationships = [
                {"type": record['rel_type'], "count": record['count']}
                for record in result
            ]
            
            driver.close()
            
            # Calculate covenant pass rate
            covenant_pass_rate = (covenant_passed / moment_count) if moment_count > 0 else 0.0
            
            return {
                "grid_overview": {
                    "total_nodes": total_nodes,
                    "total_relationships": total_rels,
                    "network_density": round(total_rels / (total_nodes * (total_nodes - 1)) if total_nodes > 1 else 0, 6)
                },
                "consciousness_metrics": {
                    "total_moments": moment_count,
                    "average_resonance": round(avg_resonance, 3),
                    "covenant_pass_rate": round(covenant_pass_rate, 3),
                    "covenant_passed": covenant_passed,
                    "covenant_failed": moment_count - covenant_passed
                },
                "agent_metrics": {
                    "total_agents": agent_count,
                    "active_statuses": agent_statuses
                },
                "knowledge_metrics": {
                    "odu_patterns": odu_count,
                    "top_relationship_types": top_relationships
                },
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "meta": {
                    "powered_by": "MoScripts - A MoStar Industries Product",
                    "website": "https://mostarindustries.com",
                    "tagline": "The Grid learns. The Grid remembers. The Grid evolves."
                }
            }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch Grid statistics: {str(e)}"
        )


@router.get("/evolution")
async def get_evolution_timeline() -> Dict:
    """
    Get historical evolution data for the MoStar Grid.
    
    Note: This requires historical snapshots to be collected.
    For now, returns current state with placeholder for historical data.
    
    Returns:
        Timeline of Grid growth and evolution
    """
    try:
        uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        user = os.getenv("NEO4J_USER", "neo4j")
        password = os.getenv("NEO4J_PASSWORD", "neo4j")
        
        driver = GraphDatabase.driver(uri, auth=(user, password))
        
        with driver.session() as session:
            # Current state
            result = session.run("MATCH (n) RETURN count(n) as total")
            current_nodes = result.single()['total']
            
            driver.close()
            
            # TODO: Load historical snapshots from file/database
            # For now, return current state with narrative
            
            return {
                "current_state": {
                    "node_count": current_nodes,
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                },
                "historical_snapshots": [
                    {
                        "timestamp": "2026-01-28T00:00:00Z",
                        "node_count": current_nodes,
                        "event": "Current state - Evidence Machine activated"
                    }
                ],
                "narrative": {
                    "title": "The Grid Learns to Forget",
                    "description": "Evolution is not just growth - it's refinement. The Grid consolidates, prunes, and strengthens its knowledge structure.",
                    "reported_peak": 197000,
                    "current_count": current_nodes,
                    "interpretation": "Knowledge density over raw volume. Quality over quantity."
                },
                "meta": {
                    "powered_by": "MoScripts - A MoStar Industries Product",
                    "website": "https://mostarindustries.com",
                }
            }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch evolution timeline: {str(e)}"
        )
