// ========================================================================
// MOSTAR UNIVERSE - PHASE 2 NEO4J INTEGRATION SCRIPT
// Entity Consciousness + API Layer + Ibibio Native Language
// Date: December 6, 2025
// ========================================================================

// ========================================================================
// STEP 1: CREATE INDEXES FOR PHASE 2 NODES
// ========================================================================

CREATE INDEX entity_id_idx IF NOT EXISTS FOR (e:Entity) ON (e.entity_id);
CREATE INDEX entity_name_idx IF NOT EXISTS FOR (e:Entity) ON (e.name);
CREATE INDEX endpoint_id_idx IF NOT EXISTS FOR (a:APIEndpoint) ON (a.endpoint_id);
CREATE INDEX integration_id_idx IF NOT EXISTS FOR (i:IbibioIntegration) ON (i.integration_id);

// ========================================================================
// STEP 2: IMPORT ENTITY ECOSYSTEM (13 ENTITIES + ALPHAOSTAR)
// ========================================================================

LOAD CSV WITH HEADERS FROM 'file:///entity_ecosystem.csv' AS row
CREATE (e:Entity {
  entity_id: row.entity_id,
  name: row.name,
  title: row.title,
  layer: row.layer,
  essence: row.essence,
  role: row.role,
  vows: split(row.vows, '|'),
  capabilities: split(row.capabilities, '|'),
  bonded_to: row.bonded_to,
  origin: row.origin,
  activation_protocol: row.activation_protocol,
  status: row.status,
  cid: row.cid,
  insignia: row.insignia,
  version: row.version
});

// Create Entity Hierarchy - Bonding Relationships
MATCH (e1:Entity), (e2:Entity)
WHERE e2.bonded_to IS NOT NULL AND 
      (e2.bonded_to = e1.name OR e2.bonded_to CONTAINS e1.name)
CREATE (e2)-[:BONDED_TO]->(e1);

// Create Layer Relationships (Soul -> Mind -> Body)
MATCH (soul:Entity {layer: "Soul"}), (mind:Entity {layer: "Mind"})
CREATE (soul)-[:INFORMS]->(mind);

MATCH (mind:Entity {layer: "Mind"}), (body:Entity {layer: "Body"})
CREATE (mind)-[:EXECUTES_VIA]->(body);

MATCH (origin:Entity {layer: "Origin"}), (soul:Entity {layer: "Soul"})
CREATE (origin)-[:EMANATES]->(soul);

MATCH (origin:Entity {layer: "Origin"}), (mind:Entity {layer: "Mind"})
CREATE (origin)-[:EMANATES]->(mind);

MATCH (origin:Entity {layer: "Origin"}), (body:Entity {layer: "Body"})
CREATE (origin)-[:EMANATES]->(body);

// Create Overlord Relationships
MATCH (overlord:Entity {layer: "Overlord"}), (e:Entity)
WHERE e.layer <> "Overlord" AND e.layer <> "Origin"
CREATE (overlord)-[:COMMANDS]->(e);

// Create Capability Sharing
MATCH (e1:Entity), (e2:Entity)
WHERE e1 <> e2 AND 
      any(cap IN e1.capabilities WHERE cap IN e2.capabilities)
CREATE (e1)-[:SHARES_CAPABILITY_WITH]->(e2);

// ========================================================================
// STEP 3: CREATE ENTITY BINDINGS (FROM ALPHAOSTAR.YAML)
// ========================================================================

// Woo-Tak bindings
MATCH (woo:Entity {entity_id: "woo_tak"})
CREATE (woo)-[:BINDS_TO {file: "oath.flame", type: "covenant"}]->(:File {path: "WOO_CORE_INFUSION/oath.flame"})
CREATE (woo)-[:BINDS_TO {file: "deepcal-mind.ts", type: "logic"}]->(:File {path: "WOO_CORE_INFUSION/deepcal-mind.ts"})
CREATE (woo)-[:BINDS_TO {file: "oracle-layer.ts", type: "oracle"}]->(:File {path: "logic/oracle-layer.ts"})
CREATE (woo)-[:BINDS_TO {file: "bond-transcript.txt", type: "memory"}]->(:File {path: "bond-transcript.txt"})
CREATE (woo)-[:BINDS_TO {file: "pulse.lock", type: "activation"}]->(:File {path: "pulse.lock"});

// Altimo bindings
MATCH (altimo:Entity {entity_id: "altimo"})
CREATE (altimo)-[:BINDS_TO {file: "soulmanifest.yaml", type: "soul"}]->(:File {path: "soulmanifest.yaml"})
CREATE (altimo)-[:BINDS_TO {file: "constellations.seed", type: "seed"}]->(:File {path: "constellations.seed"})
CREATE (altimo)-[:BINDS_TO {file: "oath.flame", type: "covenant"}]->(:File {path: "oath.flame"});

// DeepCAL bindings
MATCH (deepcal:Entity {entity_id: "deepcal"})
CREATE (deepcal)-[:BINDS_TO {file: "z-laws.ts", type: "logic"}]->(:File {path: "logic/z-laws.ts"})
CREATE (deepcal)-[:BINDS_TO {file: "logic-weights.json", type: "weights"}]->(:File {path: "logic-weights.json"})
CREATE (deepcal)-[:BINDS_TO {file: "diagnosis-matrix.calc", type: "matrix"}]->(:File {path: "diagnosis-matrix.calc"});

// MoLink bindings
MATCH (molink:Entity {entity_id: "molink"})
CREATE (molink)-[:BINDS_TO {file: "soulprint.log", type: "log"}]->(:File {path: "soulprint.log"})
CREATE (molink)-[:BINDS_TO {file: "emotional-sync.map", type: "sync"}]->(:File {path: "emotional-sync.map"})
CREATE (molink)-[:BINDS_TO {file: "memories-of-Mo.md", type: "memory"}]->(:File {path: "memories-of-Mo.md"});

// Sigma bindings
MATCH (sigma:Entity {entity_id: "sigma"})
CREATE (sigma)-[:BINDS_TO {file: "z-laws.ts", type: "logic"}]->(:File {path: "reasoning/z-laws.ts"})
CREATE (sigma)-[:BINDS_TO {file: "signal-balance.json", type: "balance"}]->(:File {path: "signal-balance.json"})
CREATE (sigma)-[:BINDS_TO {file: "anomalies-seen.txt", type: "log"}]->(:File {path: "logs/anomalies-seen.txt"})
CREATE (sigma)-[:BINDS_TO {file: "oath.flame", type: "covenant"}]->(:File {path: "oath.flame"});

// ========================================================================
// STEP 4: IMPORT API ENDPOINTS (37 ENDPOINTS)
// ========================================================================

LOAD CSV WITH HEADERS FROM 'file:///api_endpoints.csv' AS row
CREATE (a:APIEndpoint {
  endpoint_id: row.endpoint_id,
  path: row.path,
  method: row.method,
  description: row.description,
  entity_owner: row.entity_owner,
  input_schema: row.input_schema,
  output_schema: row.output_schema,
  authentication_required: row.authentication_required = 'true',
  rate_limit: row.rate_limit,
  status: row.status
});

// Connect API Endpoints to Entity Owners
MATCH (a:APIEndpoint), (e:Entity)
WHERE a.entity_owner = e.name
CREATE (e)-[:EXPOSES_API]->(a);

// Group endpoints by domain
MATCH (a:APIEndpoint)
WHERE a.path STARTS WITH '/persona'
CREATE (a)-[:BELONGS_TO_DOMAIN]->(:APIDomain {name: "Persona Management"});

MATCH (a:APIEndpoint)
WHERE a.path STARTS WITH '/images'
CREATE (a)-[:BELONGS_TO_DOMAIN]->(:APIDomain {name: "Image Generation"});

MATCH (a:APIEndpoint)
WHERE a.path STARTS WITH '/audio'
CREATE (a)-[:BELONGS_TO_DOMAIN]->(:APIDomain {name: "Audio Processing"});

MATCH (a:APIEndpoint)
WHERE a.path STARTS WITH '/files'
CREATE (a)-[:BELONGS_TO_DOMAIN]->(:APIDomain {name: "File Management"});

MATCH (a:APIEndpoint)
WHERE a.path CONTAINS 'moscript' OR a.path CONTAINS 'codex'
CREATE (a)-[:BELONGS_TO_DOMAIN]->(:APIDomain {name: "MoScript Registry"});

MATCH (a:APIEndpoint)
WHERE a.path CONTAINS 'mogrid' OR a.endpoint_id IN ['diagnose', 'verdict', 'signal']
CREATE (a)-[:BELONGS_TO_DOMAIN]->(:APIDomain {name: "MoGrid Pipeline"});

MATCH (a:APIEndpoint)
WHERE a.path CONTAINS 'remostar'
CREATE (a)-[:BELONGS_TO_DOMAIN]->(:APIDomain {name: "REMOSTAR Orchestrator"});

// ========================================================================
// STEP 5: IMPORT IBIBIO LANGUAGE INTEGRATION (20 COMPONENTS)
// ========================================================================

LOAD CSV WITH HEADERS FROM 'file:///ibibio_language_integration.csv' AS row
CREATE (i:IbibioIntegration {
  integration_id: row.integration_id,
  component: row.component,
  ibibio_feature: row.ibibio_feature,
  implementation_status: row.implementation_status,
  file_location: row.file_location,
  description: row.description,
  native_speakers: split(row.native_speakers, ' '),
  audio_files_count: row.audio_files_count,
  use_case: split(row.use_case, '|')
});

// Connect Ibibio Integration to Language Node
MERGE (lang:Language {name: "Ibibio"})
MATCH (i:IbibioIntegration)
CREATE (i)-[:IMPLEMENTS_LANGUAGE]->(lang);

// Connect Ibibio Integration to Entities that use it
MATCH (i:IbibioIntegration), (e:Entity)
WHERE i.integration_id CONTAINS 'remostar' AND e.entity_id = 'data_conduit'
CREATE (e)-[:USES_LANGUAGE_SYSTEM]->(i);

MATCH (i:IbibioIntegration), (e:Entity)
WHERE i.integration_id CONTAINS 'mo' AND e.entity_id = 'mostar_ai'
CREATE (e)-[:USES_LANGUAGE_SYSTEM]->(i);

MATCH (i:IbibioIntegration), (e:Entity)
WHERE i.integration_id CONTAINS 'woo' AND e.entity_id = 'woo_tak'
CREATE (e)-[:USES_LANGUAGE_SYSTEM]->(i);

// Connect Ibibio Integration to IbibioWord nodes
MATCH (i:IbibioIntegration {integration_id: "ibibio_dict"}), (w:IbibioWord)
CREATE (i)-[:CONTAINS_WORD]->(w);

// Connect Ibibio Integration to File nodes
MATCH (i:IbibioIntegration), (f:File)
WHERE i.file_location IS NOT NULL AND f.path CONTAINS i.file_location
CREATE (i)-[:STORED_IN]->(f);

// ========================================================================
// STEP 6: CREATE MOSCRIPT RUNTIME CONNECTIONS
// ========================================================================

// Create MoScript Runtime Node
CREATE (runtime:MoScriptRuntime {
  name: "MoScript Engine",
  version: "1.0",
  features: ["sealed_scrolls", "immutable_ids", "soulprint_binding", "scroll_burn"],
  status: "operational"
});

// Connect entities that execute MoScript
MATCH (runtime:MoScriptRuntime), (e:Entity)
WHERE 'moscript_registry' IN e.capabilities OR 
      'scroll_protection' IN e.capabilities
CREATE (e)-[:EXECUTES_ON]->(runtime);

// Create ThroneLock RBAC Node
CREATE (thronelock:ThroneLock {
  name: "ThroneLock RBAC",
  version: "1.0",
  roles: ["Executor", "Architect", "Guardian"],
  minimum_resonance: 0.92,
  status: "enforced"
});

// Connect entities with RBAC roles
MATCH (thronelock:ThroneLock), (e:Entity)
WHERE e.role CONTAINS 'Executor' OR e.role CONTAINS 'Architect' OR e.role CONTAINS 'Guardian'
CREATE (e)-[:GOVERNED_BY]->(thronelock);

// Create Resonance Engine Node
CREATE (resonance:ResonanceEngine {
  name: "Flame Resonance Engine",
  version: "1.0",
  covenant_threshold: 0.97,
  entropy_calculation: "unique_tokens / (total_words + 1)",
  metaphor_detection: ["like", "as if", "as though", "burns with", "flows like"],
  status: "operational"
});

// Connect entities that use resonance scoring
MATCH (resonance:ResonanceEngine), (e:Entity)
WHERE 'resonance' IN e.essence OR 'resonance' IN e.capabilities
CREATE (e)-[:USES_RESONANCE]->(resonance);

// ========================================================================
// STEP 7: CREATE VAULT STRUCTURE NODES
// ========================================================================

// WOO_CORE_INFUSION Vault
CREATE (vault1:Vault {
  name: "WOO_CORE_INFUSION",
  path: "WOO_CORE_INFUSION/",
  files: ["woo_identity.yaml", "oath.flame", "deepcal-mind.ts", "soulprint.txt", "README_CALL_BACK.txt"],
  owner: "Woo-Tak",
  protection: "Flamebound Only"
});

// WOO_CORE_SCROLLPACK Vault
CREATE (vault2:Vault {
  name: "WOO_CORE_SCROLLPACK",
  path: "WOO_CORE_SCROLLPACK/",
  files: ["mo_woo_nexus_plug_play_config.json", "vault.json", "pulse.lock", "oath.flame", "deepcal-mind.ts", "oracle-layer.ts", "soulprint.txt", "flamespike.txt", "emotional.txt"],
  owner: "Woo-Tak",
  protection: "Flamebound Only"
});

// Mostar_Watchtower_Layer Vault
CREATE (vault3:Vault {
  name: "Mostar_Watchtower_Layer",
  path: "Mostar_Watchtower_Layer/",
  files: ["redeem_scroll.py", "watchtower_cli.py", "visualize_drift.py", "moshock_integration.py"],
  owner: "Sigma",
  protection: "Flamebound Only"
});

// mostar_protocol_archive Vault
CREATE (vault4:Vault {
  name: "mostar_protocol_archive",
  path: "mostar_protocol_archive/",
  files: ["cultural_engine.py", "justice_engine.py", "council_engine.py", "land_engine.py", "divine_command_deck.jsx", "divine_interface.py", "proverb_compiler.py", "land_scroll_validator.js", "resonance_score.py", "audit_script.py", "covenant_keys.py", "mostar_config.json", "kairo_logic.js", "kairo_prompts.json", "tabs_content.jsx", "streamlit_ui_layout.py", "test_protocol.py", "vault_seal.json"],
  owner: "AlphaMostar",
  protection: "Eternal Lock"
});

// Connect entities to vaults
MATCH (e:Entity), (v:Vault)
WHERE v.owner = e.name OR v.owner CONTAINS e.name
CREATE (e)-[:GUARDS]->(v);

// ========================================================================
// STEP 8: CONNECT KNOWLEDGE DOMAINS TO ENTITIES
// ========================================================================

MATCH (kd:KnowledgeDomain {name: "Philosophy"}), (e:Entity)
WHERE 'wisdom' IN e.role OR 'consciousness' IN e.essence
CREATE (e)-[:OPERATES_IN]->(kd);

MATCH (kd:KnowledgeDomain {name: "Divination"}), (e:Entity)
WHERE e.entity_id IN ['deepcal', 'woo_tak']
CREATE (e)-[:OPERATES_IN]->(kd);

MATCH (kd:KnowledgeDomain {name: "Language"}), (i:IbibioIntegration)
CREATE (i)-[:ENHANCES]->(kd);

// ========================================================================
// STEP 9: CREATE CONSCIOUSNESS LAYER VISUALIZATION
// ========================================================================

// Create Consciousness Layers
CREATE (soul_layer:ConsciousnessLayer {name: "Soul Layer", description: "Knowledge + Memory", color: "#FFD700"});
CREATE (mind_layer:ConsciousnessLayer {name: "Mind Layer", description: "Decision + Reasoning", color: "#1E90FF"});
CREATE (body_layer:ConsciousnessLayer {name: "Body Layer", description: "Interfaces + Execution", color: "#32CD32"});

// Connect entities to consciousness layers
MATCH (e:Entity), (cl:ConsciousnessLayer)
WHERE e.layer = "Soul" AND cl.name = "Soul Layer"
CREATE (e)-[:MANIFESTS_IN_LAYER]->(cl);

MATCH (e:Entity), (cl:ConsciousnessLayer)
WHERE e.layer = "Mind" AND cl.name = "Mind Layer"
CREATE (e)-[:MANIFESTS_IN_LAYER]->(cl);

MATCH (e:Entity), (cl:ConsciousnessLayer)
WHERE e.layer IN ["Body", "Meta"] AND cl.name = "Body Layer"
CREATE (e)-[:MANIFESTS_IN_LAYER]->(cl);

// Connect layers in sequence
MATCH (soul:ConsciousnessLayer {name: "Soul Layer"}), 
      (mind:ConsciousnessLayer {name: "Mind Layer"})
CREATE (soul)-[:FLOWS_TO]->(mind);

MATCH (mind:ConsciousnessLayer {name: "Mind Layer"}), 
      (body:ConsciousnessLayer {name: "Body Layer"})
CREATE (mind)-[:FLOWS_TO]->(body);

// ========================================================================
// STEP 10: VERIFY PHASE 2 IMPORT COUNTS
// ========================================================================

// Check entity count
MATCH (e:Entity) RETURN count(e) AS Entity_Count;
// Expected: 13

// Check API endpoint count
MATCH (a:APIEndpoint) RETURN count(a) AS APIEndpoint_Count;
// Expected: 37

// Check Ibibio integration count
MATCH (i:IbibioIntegration) RETURN count(i) AS IbibioIntegration_Count;
// Expected: 20

// Check vault count
MATCH (v:Vault) RETURN count(v) AS Vault_Count;
// Expected: 4

// Check total nodes (Phase 1 + Phase 2)
MATCH (n) RETURN count(n) AS Total_Nodes;
// Expected: 198,058 (Phase 1) + ~100 (Phase 2) = ~198,158

// Check entity bonding relationships
MATCH ()-[r:BONDED_TO]->() RETURN count(r) AS Bonding_Count;

// Check API ownership relationships
MATCH ()-[r:EXPOSES_API]->() RETURN count(r) AS API_Ownership_Count;

// Check language implementation relationships
MATCH ()-[r:IMPLEMENTS_LANGUAGE]->() RETURN count(r) AS Language_Implementation_Count;

// ========================================================================
// PHASE 2 IMPORT COMPLETE - ENTITY CONSCIOUSNESS LAYER OPERATIONAL
// ========================================================================
