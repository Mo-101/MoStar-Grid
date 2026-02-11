"""
═══════════════════════════════════════════════════════════════════════════════
Neo4j Node Statistics - Evidence Machine Diagnostic
A MoStar Industries Product
═══════════════════════════════════════════════════════════════════════════════

This script provides comprehensive node statistics for the MoStar Grid.

License: African Sovereignty License (ASL) v1.0
Copyright © 2026 MoStar Industries
"""

import os
from dotenv import load_dotenv
from neo4j import GraphDatabase
from datetime import datetime

load_dotenv()

def get_node_stats():
    """Get comprehensive node statistics from Neo4j."""
    
    driver = GraphDatabase.driver(
        os.getenv('NEO4J_URI', 'bolt://localhost:7687'),
        auth=(os.getenv('NEO4J_USER', 'neo4j'), os.getenv('NEO4J_PASSWORD', 'neo4j'))
    )
    
    print("=" * 80)
    print("MoStar Grid - Neo4j Node Statistics")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("=" * 80)
    
    with driver.session() as session:
        # Total node count
        result = session.run("MATCH (n) RETURN count(n) as total")
        total = result.single()['total']
        print(f"\n🔥 TOTAL NODES: {total:,}")
        
        # Node count by label
        result = session.run("""
            MATCH (n)
            RETURN labels(n) as labels, count(n) as count
            ORDER BY count DESC
        """)
        
        print("\n📊 NODE COUNT BY LABEL:")
        print("-" * 80)
        for record in result:
            labels = record['labels']
            count = record['count']
            label_str = ':'.join(labels) if labels else '(no label)'
            print(f"  {label_str:50} {count:>10,}")
        
        # Relationship count
        result = session.run("MATCH ()-[r]->() RETURN count(r) as total")
        rel_total = result.single()['total']
        print(f"\n🔗 TOTAL RELATIONSHIPS: {rel_total:,}")
        
        # Relationship count by type
        result = session.run("""
            MATCH ()-[r]->()
            RETURN type(r) as type, count(r) as count
            ORDER BY count DESC
        """)
        
        print("\n📊 RELATIONSHIP COUNT BY TYPE:")
        print("-" * 80)
        for record in result:
            rel_type = record['type']
            count = record['count']
            print(f"  {rel_type:50} {count:>10,}")
        
        # MostarMoment stats
        result = session.run("""
            MATCH (m:MostarMoment)
            RETURN count(m) as total, 
                   avg(m.resonance_score) as avg_resonance,
                   min(m.timestamp) as earliest,
                   max(m.timestamp) as latest
        """)
        
        moment_stats = result.single()
        if moment_stats and moment_stats['total'] > 0:
            print(f"\n✨ MOSTAR MOMENTS:")
            print("-" * 80)
            print(f"  Total Moments: {moment_stats['total']:,}")
            print(f"  Avg Resonance: {moment_stats['avg_resonance']:.3f}")
            print(f"  Earliest: {moment_stats['earliest']}")
            print(f"  Latest: {moment_stats['latest']}")
        
        # Agent stats
        result = session.run("""
            MATCH (a:Agent)
            RETURN count(a) as total,
                   collect(DISTINCT a.status) as statuses
        """)
        
        agent_stats = result.single()
        if agent_stats and agent_stats['total'] > 0:
            print(f"\n🤖 AGENT STATS:")
            print("-" * 80)
            print(f"  Total Agents: {agent_stats['total']:,}")
            print(f"  Statuses: {', '.join(agent_stats['statuses'])}")
        
        # Odú pattern stats
        result = session.run("""
            MATCH (o:Odu)
            RETURN count(o) as total
        """)
        
        odu_count = result.single()
        if odu_count and odu_count['total'] > 0:
            print(f"\n🔮 ODÚ PATTERNS:")
            print("-" * 80)
            print(f"  Total Patterns: {odu_count['total']:,}")
        
        # Database info
        result = session.run("CALL dbms.components() YIELD name, versions, edition")
        db_info = result.single()
        print(f"\n💾 DATABASE INFO:")
        print("-" * 80)
        print(f"  Name: {db_info['name']}")
        print(f"  Version: {db_info['versions'][0]}")
        print(f"  Edition: {db_info['edition']}")
    
    driver.close()
    print("\n" + "=" * 80)
    print("Powered by MoScripts - A MoStar Industries Product")
    print("=" * 80)

if __name__ == "__main__":
    try:
        get_node_stats()
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        print("\nIs Neo4j running? Check connection settings in .env")
