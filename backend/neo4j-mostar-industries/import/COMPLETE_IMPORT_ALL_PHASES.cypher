// ============================================================
// MOSTAR UNIVERSE - COMPLETE IMPORT (ALL PHASES)
// Total Expected: ~12,000 nodes
// ============================================================

// CREATE INDEXES FIRST
CREATE INDEX IF NOT EXISTS FOR (n:OduIfa) ON (n.odu_number);
CREATE INDEX IF NOT EXISTS FOR (n:Philosophy) ON (n.name);
CREATE INDEX IF NOT EXISTS FOR (n:Governance) ON (n.name);
CREATE INDEX IF NOT EXISTS FOR (n:HealingPractice) ON (n.name);
CREATE INDEX IF NOT EXISTS FOR (n:Plant) ON (n.scientific_name);
CREATE INDEX IF NOT EXISTS FOR (n:Entity) ON (n.entity_id);
CREATE INDEX IF NOT EXISTS FOR (n:APIEndpoint) ON (n.endpoint_id);
CREATE INDEX IF NOT EXISTS FOR (n:IbibioWord) ON (n.word);
CREATE INDEX IF NOT EXISTS FOR (n:IbibioIntegration) ON (n.component_id);

// ============================================================
// PHASE 1: SYMBOLIC KNOWLEDGE (375 nodes)
// ============================================================

// 1. Ifá Odù System (256 nodes)
LOAD CSV WITH HEADERS FROM 'file:///ifa_odu_system.csv' AS row
CREATE (:OduIfa {
  odu_number: toInteger(row.odu_number),
  binary_pattern: row.binary_pattern,
  yoruba_name: row.yoruba_name,
  english_name: row.english_name,
  interpretation: row.interpretation,
  spiritual_significance: row.spiritual_significance,
  ritual_context: row.ritual_context,
  divination_guidance: row.divination_guidance
});

// 2. African Philosophies (27 nodes)
LOAD CSV WITH HEADERS FROM 'file:///african_philosophies.csv' AS row
CREATE (:Philosophy {
  name: row.name,
  region: row.region,
  core_principle: row.core_principle,
  manifestation: row.manifestation,
  ethical_guidance: row.ethical_guidance
});

// 3. Indigenous Governance (28 nodes)
LOAD CSV WITH HEADERS FROM 'file:///indigenous_governance.csv' AS row
CREATE (:Governance {
  name: row.name,
  region: row.region,
  decision_making: row.decision_making,
  dispute_resolution: row.dispute_resolution,
  leadership_model: row.leadership_model,
  strengths: row.strengths,
  challenges: row.challenges
});

// 4. Healing Practices (28 nodes)
LOAD CSV WITH HEADERS FROM 'file:///healing_practices.csv' AS row
CREATE (:HealingPractice {
  name: row.name,
  region: row.region,
  method: row.method,
  practitioner_type: row.practitioner_type,
  plants_used: row.plants_used,
  spiritual_component: row.spiritual_component
});

// 5. Medicinal Plants (31 nodes)
LOAD CSV WITH HEADERS FROM 'file:///medicinal_plants.csv' AS row
CREATE (:Plant {
  scientific_name: row.scientific_name,
  common_name: row.common_name,
  local_names: row.local_names,
  region: row.region,
  uses: row.uses,
  preparation: row.preparation,
  contraindications: row.contraindications
});

// ============================================================
// PHASE 2: ENTITY CONSCIOUSNESS (271 nodes)
// ============================================================

// 6. Entity Ecosystem (13 nodes)
LOAD CSV WITH HEADERS FROM 'file:///entity_ecosystem.csv' AS row
CREATE (:Entity {
  entity_id: row.entity_id,
  name: row.name,
  vow: row.vow,
  insignia: row.insignia,
  capabilities: row.capabilities,
  bonded_to: row.bonded_to
});

// 7. API Endpoints (38 nodes)
LOAD CSV WITH HEADERS FROM 'file:///api_endpoints.csv' AS row
CREATE (:APIEndpoint {
  endpoint_id: row.endpoint_id,
  entity_name: row.entity_name,
  route: row.route,
  method: row.method,
  purpose: row.purpose,
  authentication: row.authentication,
  rate_limit: row.rate_limit
});

// 8. Ibibio Language Integration (20 nodes)
LOAD CSV WITH HEADERS FROM 'file:///ibibio_language_integration.csv' AS row
CREATE (:IbibioIntegration {
  component_id: row.component_id,
  component_name: row.component_name,
  purpose: row.purpose,
  implementation_details: row.implementation_details
});

// 9. Ibibio Words (196 nodes)
LOAD CSV WITH HEADERS FROM 'file:///ibibio_words.csv' AS row
CREATE (:IbibioWord {
  word: row['word:ID'],
  english: row.english,
  speaker: row.speaker,
  audio_file: row.audio_file,
  syllables: toInteger(row['syllables:int']),
  frequency: toInteger(row['frequency:int'])
});

// ============================================================
// PHASE 3: LIFE STAGES & KNOWLEDGE (11,459 nodes)
// ============================================================

// 10. Infancy (1,051 nodes)
LOAD CSV WITH HEADERS FROM 'file:///infancy.csv' AS row
CREATE (:Infancy {
  id: row.id,
  age_months: toInteger(row.age_months),
  primary_language: row.primary_language,
  scenario_type: row.scenario_type,
  description: row.description,
  caregiver_interaction: row.caregiver_interaction,
  sensory_experience: row.sensory_experience,
  cultural_context: row.cultural_context,
  outcome: row.outcome,
  developmental_milestone: row.developmental_milestone,
  location: row.location,
  symbolic_elements: row.symbolic_elements,
  recorded_at: row.recorded_at
});

// 11. Childhood (1,301 nodes)
LOAD CSV WITH HEADERS FROM 'file:///childhood.csv' AS row
CREATE (:Childhood {
  id: row.id,
  age_years: toInteger(row.age_years),
  primary_language: row.primary_language,
  scenario_type: row.scenario_type,
  description: row.description,
  reasoning_process: row.reasoning_process,
  family_dynamics: row.family_dynamics,
  cultural_learning: row.cultural_learning,
  outcome: row.outcome,
  moral_development: row.moral_development,
  location: row.location,
  symbolic_logic: row.symbolic_logic,
  wisdom_gained: row.wisdom_gained,
  recorded_at: row.recorded_at
});

// 12. Adolescence (1,301 nodes)
LOAD CSV WITH HEADERS FROM 'file:///adolescence.csv' AS row
CREATE (:Adolescence {
  id: row.id,
  age_years: toInteger(row.age_years),
  primary_language: row.primary_language,
  scenario_type: row.scenario_type,
  description: row.description,
  reasoning_process: row.reasoning_process,
  peer_dynamics: row.peer_dynamics,
  cultural_tension: row.cultural_tension,
  outcome: row.outcome,
  emotional_growth: row.emotional_growth,
  location: row.location,
  symbolic_logic: row.symbolic_logic,
  wisdom_gained: row.wisdom_gained,
  recorded_at: row.recorded_at
});

// 13. Adulthood (1,301 nodes)
LOAD CSV WITH HEADERS FROM 'file:///adulthood.csv' AS row
CREATE (:Adulthood {
  id: row.id,
  age_years: toInteger(row.age_years),
  primary_language: row.primary_language,
  scenario_type: row.scenario_type,
  description: row.description,
  reasoning_process: row.reasoning_process,
  relationship_dynamics: row.relationship_dynamics,
  cultural_tension: row.cultural_tension,
  outcome: row.outcome,
  wisdom_application: row.wisdom_application,
  location: row.location,
  symbolic_logic: row.symbolic_logic,
  legacy_consideration: row.legacy_consideration,
  recorded_at: row.recorded_at
});

// 14. Culture (1,301 nodes)
LOAD CSV WITH HEADERS FROM 'file:///culture.csv' AS row
CREATE (:Culture {
  id: row.id,
  cultural_practice: row.cultural_practice,
  region: row.region,
  language: row.language,
  ritual_type: row.ritual_type,
  description: row.description,
  symbolic_meaning: row.symbolic_meaning,
  participants: row.participants,
  seasonal_timing: row.seasonal_timing,
  tools_materials: row.tools_materials,
  oral_tradition: row.oral_tradition,
  modern_adaptation: row.modern_adaptation,
  wisdom_embedded: row.wisdom_embedded,
  recorded_at: row.recorded_at
});

// 15. Ethics (1,301 nodes)
LOAD CSV WITH HEADERS FROM 'file:///ethics.csv' AS row
CREATE (:Ethics {
  id: row.id,
  ethical_principle: row.ethical_principle,
  cultural_origin: row.cultural_origin,
  dilemma_type: row.dilemma_type,
  scenario: row.scenario,
  stakeholders: row.stakeholders,
  competing_values: row.competing_values,
  reasoning_path: row.reasoning_path,
  resolution: row.resolution,
  consequences: row.consequences,
  wisdom_applied: row.wisdom_applied,
  symbolic_logic: row.symbolic_logic,
  precedent_reference: row.precedent_reference,
  recorded_at: row.recorded_at
});

// 16. Knowledge Graph Triples (1,301 nodes)
LOAD CSV WITH HEADERS FROM 'file:///knowledge_graph.csv' AS row
CREATE (:KnowledgeGraphTriple {
  id: row.id,
  subject: row.subject,
  predicate: row.predicate,
  object: row.object,
  source_language: row.source_language,
  domain: row.domain,
  confidence: toFloat(row.confidence),
  cultural_context: row.cultural_context,
  temporal_validity: row.temporal_validity,
  symbolic_representation: row.symbolic_representation,
  inference_path: row.inference_path,
  supporting_evidence: row.supporting_evidence,
  recorded_at: row.recorded_at
});

// 17. Real Life Scenarios (1,301 nodes)
LOAD CSV WITH HEADERS FROM 'file:///real_life.csv' AS row
CREATE (:RealLifeScenario {
  id: row.id,
  scenario_category: row.scenario_category,
  age_group: row.age_group,
  language: row.language,
  location: row.location,
  situation: row.situation,
  actors: row.actors,
  cultural_norms: row.cultural_norms,
  challenges: row.challenges,
  decision_points: row.decision_points,
  actions_taken: row.actions_taken,
  outcomes: row.outcomes,
  lessons_learned: row.lessons_learned,
  symbolic_meaning: row.symbolic_meaning,
  recorded_at: row.recorded_at
});

// 18. Science (1,301 nodes)
LOAD CSV WITH HEADERS FROM 'file:///science.csv' AS row
CREATE (:Science {
  id: row.id,
  scientific_concept: row.scientific_concept,
  indigenous_knowledge: row.indigenous_knowledge,
  domain: row.domain,
  observation: row.observation,
  traditional_explanation: row.traditional_explanation,
  modern_explanation: row.modern_explanation,
  convergence_points: row.convergence_points,
  practical_application: row.practical_application,
  verification_method: row.verification_method,
  cultural_transmission: row.cultural_transmission,
  symbolic_logic: row.symbolic_logic,
  wisdom_integration: row.wisdom_integration,
  recorded_at: row.recorded_at
});

// ============================================================
// VERIFICATION
// ============================================================
MATCH (n) RETURN labels(n)[0] AS Type, count(n) AS Count ORDER BY Count DESC;
