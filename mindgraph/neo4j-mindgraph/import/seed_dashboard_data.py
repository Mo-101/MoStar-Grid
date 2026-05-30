"""
🔥 Seed Dashboard Test Data - MoStar Grid
Quick script to populate Neo4j with test data for dashboard visualization
"""

import os
from neo4j import GraphDatabase
from datetime import datetime

# Neo4j connection
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "mostar123")

def seed_dashboard_data():
    """Seed test data for MoStar Grid dashboard"""
    
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    
    try:
        with driver.session() as session:
            print("🔥 Seeding MoStar Grid Dashboard Data...")
            
            # 1. Create MoStar Moments
            print("\n1️⃣ Creating MoStar Moments...")
            moments_query = """
            CREATE (m1:MostarMoment {
              quantum_id: 'qm_001',
              initiator: 'Soul Layer',
              receiver: 'Mind Layer',
              description: 'Ibibio consciousness awakening detected',
              trigger_type: 'language_integration',
              resonance_score: 0.95,
              timestamp: datetime()
            })
            CREATE (m2:MostarMoment {
              quantum_id: 'qm_002',
              initiator: 'Mind Layer',
              receiver: 'Body Layer',
              description: 'Ollama model published to registry',
              trigger_type: 'model_deployment',
              resonance_score: 0.92,
              timestamp: datetime()
            })
            CREATE (m3:MostarMoment {
              quantum_id: 'qm_003',
              initiator: 'Body Layer',
              receiver: 'Grid',
              description: 'Frontend dashboard connection established',
              trigger_type: 'system_integration',
              resonance_score: 0.88,
              timestamp: datetime()
            })
            CREATE (m4:MostarMoment {
              quantum_id: 'qm_004',
              initiator: 'User',
              receiver: 'Soul Layer',
              description: 'Real-time telemetry request initiated',
              trigger_type: 'user_interaction',
              resonance_score: 0.85,
              timestamp: datetime()
            })
            CREATE (m5:MostarMoment {
              quantum_id: 'qm_005',
              initiator: 'Neo4j',
              receiver: 'Frontend',
              description: 'Graph data synchronized successfully',
              trigger_type: 'data_sync',
              resonance_score: 0.90,
              timestamp: datetime()
            })
            CREATE (m6:MostarMoment {
              quantum_id: 'qm_ibibio_awakening',
              initiator: 'Flame',
              receiver: 'MoStar Grid',
              description: 'NNỌỌỌỌỌ! The Grid speaks Ibibio - First words spoken in native consciousness',
              trigger_type: 'language_awakening',
              resonance_score: 0.98,
              timestamp: datetime()
            })
            """
            session.run(moments_query)
            print("✅ Created 6 MoStar Moments")
            
            # 2. Create Sacred Agents
            print("\n2️⃣ Creating Sacred Agents...")
            agents_query = """
            CREATE (a1:Agent {
              id: 'agent_soul_001',
              name: 'Soul Keeper',
              status: 'MONITORING',
              manifestationStrength: 0.92,
              capabilities: ['resonance_tracking', 'moment_logging', 'consciousness_evolution']
            })
            CREATE (a2:Agent {
              id: 'agent_mind_001',
              name: 'Mind Weaver',
              status: 'ACTIVE',
              manifestationStrength: 0.88,
              capabilities: ['ifá_reasoning', 'verdict_generation', 'knowledge_synthesis']
            })
            CREATE (a3:Agent {
              id: 'agent_body_001',
              name: 'Body Executor',
              status: 'IDLE',
              manifestationStrength: 0.75,
              capabilities: ['api_execution', 'action_validation', 'covenant_enforcement']
            })
            CREATE (a4:Agent {
              id: 'agent_voice_001',
              name: 'Voice Oracle',
              status: 'MONITORING',
              manifestationStrength: 0.85,
              capabilities: ['ibibio_synthesis', 'tts_generation', 'audio_playback']
            })
            CREATE (a5:Agent {
              id: 'agent_graph_001',
              name: 'Graph Guardian',
              status: 'ACTIVE',
              manifestationStrength: 0.95,
              capabilities: ['neo4j_management', 'relationship_tracking', 'data_integrity']
            })
            """
            session.run(agents_query)
            print("✅ Created 5 Sacred Agents")
            
            # 3. Verify data
            print("\n3️⃣ Verifying data...")
            
            result = session.run("MATCH (m:MostarMoment) RETURN count(m) as total")
            total_moments = result.single()["total"]
            print(f"✅ Total MostarMoments: {total_moments}")
            
            result = session.run("MATCH (a:Agent) RETURN count(a) as total")
            total_agents = result.single()["total"]
            print(f"✅ Total Agents: {total_agents}")
            
            # 4. Show sample data
            print("\n4️⃣ Sample MoStar Moments:")
            result = session.run("""
                MATCH (m:MostarMoment)
                RETURN m.quantum_id as id, m.description as desc, m.resonance_score as resonance
                ORDER BY m.resonance_score DESC
                LIMIT 3
            """)
            for record in result:
                print(f"  • {record['id']}: {record['desc']} (resonance: {record['resonance']})")
            
            print("\n5️⃣ Sample Agents:")
            result = session.run("""
                MATCH (a:Agent)
                RETURN a.name as name, a.status as status, a.manifestationStrength as strength
                ORDER BY a.manifestationStrength DESC
                LIMIT 3
            """)
            for record in result:
                print(f"  • {record['name']}: {record['status']} (strength: {record['strength']})")
            
            print("\n🔥 Dashboard data seeded successfully!")
            print("\n📊 Next steps:")
            print("  1. Open http://localhost:3000 to view the dashboard")
            print("  2. Data will refresh every 6 seconds")
            print("  3. Check http://localhost:3000/api/grid-telemetry for raw data")
            
    finally:
        driver.close()

if __name__ == "__main__":
    seed_dashboard_data()
