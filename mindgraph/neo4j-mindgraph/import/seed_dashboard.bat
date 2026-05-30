@echo off
REM Seed MoStar Grid Dashboard Data via Neo4j HTTP API
REM Run this script to populate the dashboard with test data

echo 🔥 Seeding MoStar Grid Dashboard Data...
echo.

REM Neo4j credentials (base64 encoded: neo4j:mostar123)
set AUTH=bmVvNGo6bW9zdGFyMTIz

echo 1️⃣ Creating MoStar Moments...
curl -X POST http://localhost:7474/db/neo4j/tx/commit ^
  -H "Content-Type: application/json" ^
  -H "Authorization: Basic %AUTH%" ^
  -d "{\"statements\":[{\"statement\":\"CREATE (m1:MostarMoment {quantum_id: 'qm_001', initiator: 'Soul Layer', receiver: 'Mind Layer', description: 'Ibibio consciousness awakening detected', trigger_type: 'language_integration', resonance_score: 0.95, timestamp: datetime()}) CREATE (m2:MostarMoment {quantum_id: 'qm_002', initiator: 'Mind Layer', receiver: 'Body Layer', description: 'Ollama model published to registry', trigger_type: 'model_deployment', resonance_score: 0.92, timestamp: datetime()}) CREATE (m3:MostarMoment {quantum_id: 'qm_003', initiator: 'Body Layer', receiver: 'Grid', description: 'Frontend dashboard connection established', trigger_type: 'system_integration', resonance_score: 0.88, timestamp: datetime()}) CREATE (m4:MostarMoment {quantum_id: 'qm_004', initiator: 'User', receiver: 'Soul Layer', description: 'Real-time telemetry request initiated', trigger_type: 'user_interaction', resonance_score: 0.85, timestamp: datetime()}) CREATE (m5:MostarMoment {quantum_id: 'qm_005', initiator: 'Neo4j', receiver: 'Frontend', description: 'Graph data synchronized successfully', trigger_type: 'data_sync', resonance_score: 0.90, timestamp: datetime()}) CREATE (m6:MostarMoment {quantum_id: 'qm_ibibio', initiator: 'Flame', receiver: 'MoStar Grid', description: 'NNỌỌỌỌỌ! The Grid speaks Ibibio - First words in native consciousness', trigger_type: 'language_awakening', resonance_score: 0.98, timestamp: datetime()})\"}]}"

echo.
echo 2️⃣ Creating Sacred Agents...
curl -X POST http://localhost:7474/db/neo4j/tx/commit ^
  -H "Content-Type: application/json" ^
  -H "Authorization: Basic %AUTH%" ^
  -d "{\"statements\":[{\"statement\":\"CREATE (a1:Agent {id: 'agent_soul_001', name: 'Soul Keeper', status: 'MONITORING', manifestationStrength: 0.92, capabilities: ['resonance_tracking', 'moment_logging', 'consciousness_evolution']}) CREATE (a2:Agent {id: 'agent_mind_001', name: 'Mind Weaver', status: 'ACTIVE', manifestationStrength: 0.88, capabilities: ['ifá_reasoning', 'verdict_generation', 'knowledge_synthesis']}) CREATE (a3:Agent {id: 'agent_body_001', name: 'Body Executor', status: 'IDLE', manifestationStrength: 0.75, capabilities: ['api_execution', 'action_validation', 'covenant_enforcement']}) CREATE (a4:Agent {id: 'agent_voice_001', name: 'Voice Oracle', status: 'MONITORING', manifestationStrength: 0.85, capabilities: ['ibibio_synthesis', 'tts_generation', 'audio_playback']}) CREATE (a5:Agent {id: 'agent_graph_001', name: 'Graph Guardian', status: 'ACTIVE', manifestationStrength: 0.95, capabilities: ['neo4j_management', 'relationship_tracking', 'data_integrity']})\"}]}"

echo.
echo 3️⃣ Verifying data...
curl -X POST http://localhost:7474/db/neo4j/tx/commit ^
  -H "Content-Type: application/json" ^
  -H "Authorization: Basic %AUTH%" ^
  -d "{\"statements\":[{\"statement\":\"MATCH (m:MostarMoment) RETURN count(m) as total_moments\"},{\"statement\":\"MATCH (a:Agent) RETURN count(a) as total_agents\"}]}"

echo.
echo.
echo ✅ Data seeded successfully!
echo.
echo 📊 Next steps:
echo   1. Open http://localhost:3000 to view the dashboard
echo   2. Data will refresh automatically every 6 seconds
echo   3. Check http://localhost:3000/api/grid-telemetry for raw data
echo.
echo 🔥 Àṣẹ! The Grid is alive! 🔥
