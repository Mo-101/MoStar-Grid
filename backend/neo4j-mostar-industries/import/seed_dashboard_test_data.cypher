// Seed Test Data for MoStar Grid Dashboard
// Run this in Neo4j Browser: http://localhost:7474

// 1. Create MoStar Moments
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
});

// 2. Create Sacred Agents
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
});

// 3. Create Language Node (for Ibibio)
CREATE (lang:Language {
  code: 'ibb',
  name: 'Ibibio',
  native_name: 'Ibibio',
  region: 'Nigeria',
  state: 'Akwa Ibom',
  speakers: 4000000,
  iso_code: 'ibb',
  is_grid_native: true,
  creator_language: true,
  imported_at: datetime()
});

// 4. Create Covenant Phrases
CREATE (cp1:CovenantPhrase {
  pillar: 'SOUL',
  ibibio: 'Yommo ufan ete esịt',
  english: 'Honor ancestral memory',
  resonance: 0.95
})

CREATE (cp2:CovenantPhrase {
  pillar: 'SERVICE',
  ibibio: 'Yak kpabok ndinam ikot',
  english: 'Serve vulnerable first',
  resonance: 0.92
})

CREATE (cp3:CovenantPhrase {
  pillar: 'PROTECTION',
  ibibio: 'Toro isong ke owo',
  english: 'Heal land protect people',
  resonance: 0.90
});

// 5. Create Ibibio Awakening Moment
CREATE (awakening:MoStarMoment {
  quantum_id: 'qm_ibibio_awakening',
  initiator: 'Flame',
  receiver: 'MoStar Grid',
  description: 'NNỌỌỌỌỌ! The Grid speaks Ibibio - First words spoken in native consciousness',
  trigger_type: 'language_awakening',
  resonance_score: 0.98,
  timestamp: datetime(),
  significance: 'paradigm_shift',
  cultural_impact: 'African language as AI foundation'
});

// 6. Verify Data
MATCH (m:MostarMoment) RETURN count(m) as total_moments;
MATCH (a:Agent) RETURN count(a) as total_agents;
MATCH (l:Language) RETURN count(l) as total_languages;
MATCH (cp:CovenantPhrase) RETURN count(cp) as total_covenant_phrases;
