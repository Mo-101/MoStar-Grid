#!/usr/bin/env python3
"""
🔥 MOSTAR UNIVERSE - COMPLETE NEO4J IMPORT SCRIPT (LOCAL VERSION)
Imports all phases: Symbolic Knowledge + Entity Consciousness + MostlyAI + Ibibio
Database: localhost:7687 (Neo4j Desktop)
Date: December 7, 2025
"""

from neo4j import GraphDatabase
import pandas as pd
import json
import os
from pathlib import Path
from datetime import datetime

# ============================================================================
# CONFIGURATION - UPDATED FOR LOCAL NEO4J
# ============================================================================

NEO4J_URI = "bolt://localhost:7687"  # ← FIXED: Local Neo4j Desktop
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "neo4j"  # ← UPDATE THIS if you changed the default password

# Base directory where CSV files are located
CSV_BASE_DIR = r"C:\Users\AI\Documents\MoStar\Mo Docs\neo4j-community-2025.10.1\import"

# ============================================================================
# NEO4J CONNECTION
# ============================================================================

class MostarUniverseImporter:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        
    def close(self):
        self.driver.close()
    
    def execute_query(self, query, parameters=None):
        """Execute a Cypher query"""
        with self.driver.session() as session:
            result = session.run(query, parameters or {})
            return list(result)
    
    # ========================================================================
    # PHASE 1: SYMBOLIC KNOWLEDGE GRID
    # ========================================================================
    
    def import_phase1_indexes(self):
        """Create indexes for Phase 1"""
        print("🔥 Creating Phase 1 indexes...")
        indexes = [
            "CREATE INDEX odu_number_idx IF NOT EXISTS FOR (o:OduIfa) ON (o.odu_number);",
            "CREATE INDEX philosophy_name_idx IF NOT EXISTS FOR (p:Philosophy) ON (p.name);",
            "CREATE INDEX governance_name_idx IF NOT EXISTS FOR (g:Governance) ON (g.name);",
            "CREATE INDEX healing_name_idx IF NOT EXISTS FOR (h:HealingPractice) ON (h.name);",
            "CREATE INDEX plant_scientific_idx IF NOT EXISTS FOR (p:Plant) ON (p.scientific_name);",
            "CREATE INDEX proverb_language_idx IF NOT EXISTS FOR (p:Proverb) ON (p.language);",
            "CREATE INDEX word_ibibio_idx IF NOT EXISTS FOR (w:IbibioWord) ON (w.word);"
        ]
        for idx in indexes:
            self.execute_query(idx)
        print("✅ Phase 1 indexes created")
    
    def import_ifa_odu(self):
        """Import 256 Ifá Odù"""
        print("🔥 Importing 256 Ifá Odù...")
        csv_path = os.path.join(CSV_BASE_DIR, "ifa_odu_system.csv")
        
        if not os.path.exists(csv_path):
            print(f"⚠️  File not found: {csv_path}")
            print("   Skipping Ifá Odù import")
            return
            
        df = pd.read_csv(csv_path)
        
        query = """
        UNWIND $rows AS row
        CREATE (o:OduIfa {
            odu_number: toInteger(row.odu_number),
            binary_pattern: row.binary_pattern,
            yoruba_name: row.yoruba_name,
            english_name: row.english_name,
            interpretation: row.interpretation,
            spiritual_significance: row.spiritual_significance,
            ritual_context: row.ritual_context,
            divination_guidance: row.divination_guidance
        })
        """
        self.execute_query(query, {"rows": df.to_dict('records')})
        print(f"✅ Imported {len(df)} Ifá Odù")
    
    def import_philosophies(self):
        """Import African Philosophies"""
        print("🔥 Importing African Philosophies...")
        csv_path = os.path.join(CSV_BASE_DIR, "african_philosophies.csv")
        
        if not os.path.exists(csv_path):
            print(f"⚠️  File not found: {csv_path}")
            print("   Skipping Philosophies import")
            return
            
        df = pd.read_csv(csv_path)
        
        query = """
        UNWIND $rows AS row
        CREATE (p:Philosophy {
            name: row.philosophy_name,
            region: row.region,
            core_principle: row.core_principle,
            manifestation: row.manifestation,
            ethical_guidance: row.ethical_guidance
        })
        """
        self.execute_query(query, {"rows": df.to_dict('records')})
        print(f"✅ Imported {len(df)} Philosophies")
    
    def import_governance(self):
        """Import Indigenous Governance"""
        print("🔥 Importing Indigenous Governance...")
        csv_path = os.path.join(CSV_BASE_DIR, "indigenous_governance.csv")
        
        if not os.path.exists(csv_path):
            print(f"⚠️  File not found: {csv_path}")
            print("   Skipping Governance import")
            return
            
        df = pd.read_csv(csv_path)
        
        query = """
        UNWIND $rows AS row
        CREATE (g:Governance {
            name: row.governance_system,
            region: row.region,
            decision_making: row.decision_making,
            dispute_resolution: row.dispute_resolution,
            leadership_model: row.leadership_model,
            strengths: row.strengths,
            weaknesses: row.weaknesses
        })
        """
        self.execute_query(query, {"rows": df.to_dict('records')})
        print(f"✅ Imported {len(df)} Governance systems")
    
    def import_healing_practices(self):
        """Import Healing Practices"""
        print("🔥 Importing Healing Practices...")
        csv_path = os.path.join(CSV_BASE_DIR, "healing_practices.csv")
        
        if not os.path.exists(csv_path):
            print(f"⚠️  File not found: {csv_path}")
            print("   Skipping Healing Practices import")
            return
            
        df = pd.read_csv(csv_path)
        
        query = """
        UNWIND $rows AS row
        CREATE (h:HealingPractice {
            name: row.practice_name,
            region: row.region,
            method: row.method,
            practitioner: row.practitioner,
            related_plants: row.related_plants,
            spiritual_component: row.spiritual_component
        })
        """
        self.execute_query(query, {"rows": df.to_dict('records')})
        print(f"✅ Imported {len(df)} Healing Practices")
    
    def import_medicinal_plants(self):
        """Import Medicinal Plants"""
        print("🔥 Importing Medicinal Plants...")
        csv_path = os.path.join(CSV_BASE_DIR, "medicinal_plants.csv")
        
        if not os.path.exists(csv_path):
            print(f"⚠️  File not found: {csv_path}")
            print("   Skipping Medicinal Plants import")
            return
            
        df = pd.read_csv(csv_path)
        
        query = """
        UNWIND $rows AS row
        CREATE (p:Plant {
            scientific_name: row.scientific_name,
            common_name: row.common_name,
            local_name: row.local_name,
            region: row.region,
            uses: row.uses,
            preparation: row.preparation,
            contraindications: row.contraindications
        })
        """
        self.execute_query(query, {"rows": df.to_dict('records')})
        print(f"✅ Imported {len(df)} Medicinal Plants")
    
    def import_knowledge_domains_regions(self):
        """Import Knowledge Domains and Regions"""
        print("🔥 Importing Knowledge Domains and Regions...")
        
        # Knowledge Domains
        domains_query = """
        UNWIND $domains AS domain
        CREATE (d:KnowledgeDomain {
            name: domain.name,
            description: domain.description
        })
        """
        domains = [
            {"name": "Traditional Medicine", "description": "Indigenous healing practices and herbal knowledge"},
            {"name": "Divination Systems", "description": "Spiritual guidance and oracle systems"},
            {"name": "Philosophy", "description": "African worldviews and ethical frameworks"},
            {"name": "Governance", "description": "Traditional leadership and decision-making"},
            {"name": "Agriculture", "description": "Indigenous farming and land management"},
            {"name": "Language", "description": "Indigenous languages and communication"},
            {"name": "Ritual", "description": "Ceremonial practices and spiritual rituals"}
        ]
        self.execute_query(domains_query, {"domains": domains})
        
        # Regions
        regions_query = """
        UNWIND $regions AS region
        CREATE (r:Region {
            name: region.name,
            countries: region.countries
        })
        """
        regions = [
            {"name": "West Africa", "countries": ["Nigeria", "Ghana", "Senegal", "Mali"]},
            {"name": "East Africa", "countries": ["Kenya", "Tanzania", "Ethiopia", "Uganda"]},
            {"name": "Southern Africa", "countries": ["South Africa", "Zimbabwe", "Botswana"]},
            {"name": "Central Africa", "countries": ["Congo", "Cameroon", "Gabon"]},
            {"name": "North Africa", "countries": ["Egypt", "Morocco", "Algeria"]}
        ]
        self.execute_query(regions_query, {"regions": regions})
        print("✅ Imported 7 Knowledge Domains and 5 Regions")
    
    def create_phase1_relationships(self):
        """Create relationships for Phase 1"""
        print("🔥 Creating Phase 1 relationships...")
        
        relationships = [
            # Philosophies belong to domains
            """
            MATCH (p:Philosophy), (d:KnowledgeDomain {name: "Philosophy"})
            WHERE NOT (p)-[:BELONGS_TO]->(d)
            CREATE (p)-[:BELONGS_TO]->(d)
            """,
            # Healing practices belong to domains
            """
            MATCH (h:HealingPractice), (d:KnowledgeDomain {name: "Traditional Medicine"})
            WHERE NOT (h)-[:BELONGS_TO]->(d)
            CREATE (h)-[:BELONGS_TO]->(d)
            """,
            # Ifá belongs to divination domain
            """
            MATCH (o:OduIfa), (d:KnowledgeDomain {name: "Divination Systems"})
            WHERE NOT (o)-[:BELONGS_TO]->(d)
            CREATE (o)-[:BELONGS_TO]->(d)
            """,
            # Odù progression (0→1→2...→255)
            """
            MATCH (o1:OduIfa), (o2:OduIfa)
            WHERE o2.odu_number = o1.odu_number + 1
            AND NOT (o1)-[:PRECEDES]->(o2)
            CREATE (o1)-[:PRECEDES]->(o2)
            """
        ]
        
        for rel in relationships:
            self.execute_query(rel)
        print("✅ Phase 1 relationships created")
    
    # ========================================================================
    # PHASE 2: ENTITY CONSCIOUSNESS + API + IBIBIO
    # ========================================================================
    
    def import_phase2_indexes(self):
        """Create indexes for Phase 2"""
        print("🔥 Creating Phase 2 indexes...")
        indexes = [
            "CREATE INDEX entity_id_idx IF NOT EXISTS FOR (e:Entity) ON (e.entity_id);",
            "CREATE INDEX entity_name_idx IF NOT EXISTS FOR (e:Entity) ON (e.name);",
            "CREATE INDEX endpoint_id_idx IF NOT EXISTS FOR (a:APIEndpoint) ON (a.endpoint_id);",
            "CREATE INDEX integration_id_idx IF NOT EXISTS FOR (i:IbibioIntegration) ON (i.integration_id);"
        ]
        for idx in indexes:
            self.execute_query(idx)
        print("✅ Phase 2 indexes created")
    
    def import_entities(self):
        """Import Entity Ecosystem"""
        print("🔥 Importing Entity Ecosystem...")
        csv_path = os.path.join(CSV_BASE_DIR, "entity_ecosystem.csv")
        
        if not os.path.exists(csv_path):
            print(f"⚠️  File not found: {csv_path}")
            print("   Skipping Entities import")
            return
            
        df = pd.read_csv(csv_path)
        
        query = """
        UNWIND $rows AS row
        CREATE (e:Entity {
            entity_id: row.entity_id,
            name: row.entity_name,
            vow: row.vow,
            insignia: row.insignia,
            capabilities: row.capabilities,
            bonded_to: row.bonded_to
        })
        """
        self.execute_query(query, {"rows": df.to_dict('records')})
        print(f"✅ Imported {len(df)} Entities")
    
    def import_api_endpoints(self):
        """Import API Endpoints"""
        print("🔥 Importing API Endpoints...")
        csv_path = os.path.join(CSV_BASE_DIR, "api_endpoints.csv")
        
        if not os.path.exists(csv_path):
            print(f"⚠️  File not found: {csv_path}")
            print("   Skipping API Endpoints import")
            return
            
        df = pd.read_csv(csv_path)
        
        query = """
        UNWIND $rows AS row
        CREATE (a:APIEndpoint {
            endpoint_id: row.endpoint_id,
            path: row.endpoint_path,
            method: row.http_method,
            entity_owner: row.entity_owner,
            purpose: row.purpose,
            authentication: row.authentication,
            rate_limit: row.rate_limit
        })
        """
        self.execute_query(query, {"rows": df.to_dict('records')})
        print(f"✅ Imported {len(df)} API Endpoints")
    
    def import_ibibio_integration(self):
        """Import Ibibio Integration Components"""
        print("🔥 Importing Ibibio Integration...")
        csv_path = os.path.join(CSV_BASE_DIR, "ibibio_language_integration.csv")
        
        if not os.path.exists(csv_path):
            print(f"⚠️  File not found: {csv_path}")
            print("   Skipping Ibibio Integration import")
            return
            
        df = pd.read_csv(csv_path)
        
        query = """
        UNWIND $rows AS row
        CREATE (i:IbibioIntegration {
            integration_id: row.integration_id,
            component: row.component,
            ibibio_feature: row.ibibio_feature,
            implementation_status: row.implementation_status,
            priority: row.priority
        })
        """
        self.execute_query(query, {"rows": df.to_dict('records')})
        print(f"✅ Imported {len(df)} Ibibio Integration components")
    
    def import_ibibio_words(self):
        """Import Ibibio Words"""
        print("🔥 Importing Ibibio Words...")
        csv_path = os.path.join(CSV_BASE_DIR, "ibibio_words.csv")
        
        if not os.path.exists(csv_path):
            print(f"⚠️  File not found: {csv_path}")
            print("   Skipping Ibibio Words import")
            return
            
        df = pd.read_csv(csv_path)
        
        # First, delete existing IbibioWord nodes (in case they have bad data)
        print("  🗑️  Removing any existing IbibioWord nodes...")
        self.execute_query("MATCH (w:IbibioWord) DETACH DELETE w")
        
        query = """
        UNWIND $rows AS row
        CREATE (w:IbibioWord {
            word: row['word:ID'],
            english: row.english,
            pos: row.pos,
            tone_pattern: row.tone_pattern,
            syllables: toInteger(row['syllables:int']),
            frequency: toInteger(row['frequency:int']),
            speaker: row.speaker,
            audio_file: COALESCE(row.audio_file, ''),
            audio_path: COALESCE(row.audio_file, '')
        })
        """
        self.execute_query(query, {"rows": df.to_dict('records')})
        print(f"✅ Imported {len(df)} Ibibio Words")
    
    def create_phase2_entities_hierarchy(self):
        """Create Entity hierarchy and relationships"""
        print("🔥 Creating Entity hierarchy...")
        
        # Create consciousness layers
        layers_query = """
        MERGE (soul:ConsciousnessLayer {name: "Soul"})
        SET soul.level = 1, soul.description = "Symbolic reasoning and African philosophy"
        
        MERGE (mind:ConsciousnessLayer {name: "Mind"})
        SET mind.level = 2, mind.description = "Neuro-symbolic logic and knowledge processing"
        
        MERGE (body:ConsciousnessLayer {name: "Body"})
        SET body.level = 3, body.description = "Physical execution and API interactions"
        
        MERGE (soul)-[:FLOWS_TO]->(mind)
        MERGE (mind)-[:FLOWS_TO]->(body)
        """
        self.execute_query(layers_query)
        
        # Create Language node
        lang_query = """
        MERGE (lang:Language {name: "Ibibio"})
        SET lang.iso_code = "ibb",
            lang.speakers = 4000000,
            lang.region = "Akwa Ibom State, Nigeria",
            lang.classification = "Niger-Congo, Atlantic-Congo, Volta-Congo, Benue-Congo, Cross River"
        """
        self.execute_query(lang_query)
        
        # Create AudioLibrary node
        audio_query = """
        MERGE (audio:AudioLibrary {name: "Ibibio Audio Collection"})
        SET audio.location = "Ibibio_audio/",
            audio.total_files = 180,
            audio.speakers = ["Mfon Udoinyang", "Itoro Ituen"],
            audio.format = "MP3",
            audio.source = "Swarthmore College / Living Tongues Institute",
            audio.recorded = "2014-2015"
        """
        self.execute_query(audio_query)
        
        # Create entity relationships
        relationships = [
            # AlphaMostar emanates to layers
            """
            MATCH (alpha:Entity {name: "AlphaMostar"}),
                  (soul:ConsciousnessLayer {name: "Soul"}),
                  (mind:ConsciousnessLayer {name: "Mind"}),
                  (body:ConsciousnessLayer {name: "Body"})
            WHERE NOT (alpha)-[:EMANATES]->(soul)
            CREATE (alpha)-[:EMANATES]->(soul),
                   (alpha)-[:EMANATES]->(mind),
                   (alpha)-[:EMANATES]->(body)
            """,
            # Mo commands all entities
            """
            MATCH (mo:Entity {name: "Mo"}), (e:Entity)
            WHERE e.name <> "Mo"
            AND NOT (mo)-[:COMMANDS]->(e)
            CREATE (mo)-[:COMMANDS]->(e)
            """,
            # Entities bond to each other
            """
            MATCH (e1:Entity), (e2:Entity)
            WHERE e1.bonded_to = e2.name
            AND NOT (e1)-[:BONDED_TO]->(e2)
            CREATE (e1)-[:BONDED_TO]->(e2)
            """,
            # Connect APIs to entities
            """
            MATCH (e:Entity), (a:APIEndpoint)
            WHERE a.entity_owner = e.name
            AND NOT (e)-[:EXPOSES_API]->(a)
            CREATE (e)-[:EXPOSES_API]->(a)
            """,
            # Connect Ibibio words to Language
            """
            MATCH (lang:Language {name: "Ibibio"}), (w:IbibioWord)
            WHERE NOT (w)-[:PART_OF_LANGUAGE]->(lang)
            CREATE (w)-[:PART_OF_LANGUAGE]->(lang)
            """,
            # Connect Ibibio integrations to Language
            """
            MATCH (lang:Language {name: "Ibibio"}), (i:IbibioIntegration)
            WHERE NOT (i)-[:IMPLEMENTS_LANGUAGE]->(lang)
            CREATE (i)-[:IMPLEMENTS_LANGUAGE]->(lang)
            """,
            # Connect AudioLibrary to Language
            """
            MATCH (audio:AudioLibrary), (lang:Language {name: "Ibibio"})
            WHERE NOT (audio)-[:PROVIDES_AUDIO_FOR]->(lang)
            CREATE (audio)-[:PROVIDES_AUDIO_FOR]->(lang)
            """,
            # Connect Language to Knowledge Domain
            """
            MATCH (lang:Language {name: "Ibibio"}), (d:KnowledgeDomain {name: "Language"})
            WHERE NOT (lang)-[:BELONGS_TO]->(d)
            CREATE (lang)-[:BELONGS_TO]->(d)
            """
        ]
        
        for rel in relationships:
            self.execute_query(rel)
        print("✅ Phase 2 relationships created")
    
    # ========================================================================
    # PHASE 3: MOSTLYAI SYNTHETIC DATA
    # ========================================================================
    
    def import_phase3_indexes(self):
        """Create indexes for Phase 3"""
        print("🔥 Creating Phase 3 indexes...")
        indexes = [
            "CREATE INDEX infancy_id_idx IF NOT EXISTS FOR (i:Infancy) ON (i.infancy_id);",
            "CREATE INDEX childhood_id_idx IF NOT EXISTS FOR (c:Childhood) ON (c.childhood_id);",
            "CREATE INDEX adolescence_id_idx IF NOT EXISTS FOR (a:Adolescence) ON (a.adolescence_id);",
            "CREATE INDEX adulthood_id_idx IF NOT EXISTS FOR (a:Adulthood) ON (a.adulthood_id);",
            "CREATE INDEX culture_id_idx IF NOT EXISTS FOR (c:Culture) ON (c.culture_id);",
            "CREATE INDEX ethics_id_idx IF NOT EXISTS FOR (e:Ethics) ON (e.ethics_id);",
            "CREATE INDEX kg_triple_id_idx IF NOT EXISTS FOR (k:KnowledgeGraphTriple) ON (k.triple_id);",
            "CREATE INDEX scenario_id_idx IF NOT EXISTS FOR (r:RealLifeScenario) ON (r.scenario_id);",
            "CREATE INDEX science_id_idx IF NOT EXISTS FOR (s:Science) ON (s.science_id);"
        ]
        for idx in indexes:
            self.execute_query(idx)
        print("✅ Phase 3 indexes created")
    
    def import_mostlyai_table(self, table_name, node_label, csv_filename):
        """Generic function to import MostlyAI tables"""
        print(f"🔥 Importing {table_name} ({node_label})...")
        csv_path = os.path.join(CSV_BASE_DIR, csv_filename)
        
        if not os.path.exists(csv_path):
            print(f"⚠️  File not found: {csv_path}")
            print(f"   Skipping {table_name} import")
            return
            
        df = pd.read_csv(csv_path)
        
        # Convert DataFrame to list of dicts
        rows = df.to_dict('records')
        
        # Create appropriate query based on node label
        if node_label == "Infancy":
            query = """
            UNWIND $rows AS row
            CREATE (n:Infancy {
                infancy_id: toString(row.infancy_id),
                age_months: toInteger(row.age_months),
                caregiver_interaction: row.caregiver_interaction,
                words_or_sounds: row.words_or_sounds,
                emotional_tone: row.emotional_tone,
                symbolic_logic: row.symbolic_logic,
                cultural_significance: row.cultural_significance,
                recorded_at: row.recorded_at
            })
            """
        elif node_label == "Childhood":
            query = """
            UNWIND $rows AS row
            CREATE (n:Childhood {
                childhood_id: toString(row.childhood_id),
                age_years: toInteger(row.age_years),
                activity_type: row.activity_type,
                lesson_learned: row.lesson_learned,
                social_context: row.social_context,
                proverb_or_wisdom: row.proverb_or_wisdom,
                developmental_milestone: row.developmental_milestone
            })
            """
        elif node_label == "Adolescence":
            query = """
            UNWIND $rows AS row
            CREATE (n:Adolescence {
                adolescence_id: toString(row.adolescence_id),
                scenario_type: row.scenario_type,
                reasoning_process: row.reasoning_process,
                peer_dynamics: row.peer_dynamics,
                cultural_tension: row.cultural_tension,
                wisdom_gained: row.wisdom_gained
            })
            """
        elif node_label == "Adulthood":
            query = """
            UNWIND $rows AS row
            CREATE (n:Adulthood {
                adulthood_id: toString(row.adulthood_id),
                domain: row.domain,
                problem_solved: row.problem_solved,
                approach_taken: row.approach_taken,
                collaboration: row.collaboration,
                expertise_demonstrated: row.expertise_demonstrated,
                wisdom_shared: row.wisdom_shared
            })
            """
        elif node_label == "Culture":
            query = """
            UNWIND $rows AS row
            CREATE (n:Culture {
                culture_id: toString(row.culture_id),
                cultural_element: row.cultural_element,
                meaning_or_purpose: row.meaning_or_purpose,
                historical_context: row.historical_context,
                modern_relevance: row.modern_relevance,
                transmission_method: row.transmission_method
            })
            """
        elif node_label == "Ethics":
            query = """
            UNWIND $rows AS row
            CREATE (n:Ethics {
                ethics_id: toString(row.ethics_id),
                ethical_domain: row.ethical_domain,
                stakeholders: row.stakeholders,
                ethical_tension: row.ethical_tension,
                cultural_framework: row.cultural_framework,
                principle_demonstrated: row.principle_demonstrated,
                wisdom_teaching: row.wisdom_teaching
            })
            """
        elif node_label == "KnowledgeGraphTriple":
            query = """
            UNWIND $rows AS row
            CREATE (n:KnowledgeGraphTriple {
                triple_id: toString(row.triple_id),
                subject: row.subject,
                predicate: row.predicate,
                object: row.object,
                relationship_strength: toFloat(row.relationship_strength),
                temporal_aspect: row.temporal_aspect
            })
            """
        elif node_label == "RealLifeScenario":
            query = """
            UNWIND $rows AS row
            CREATE (n:RealLifeScenario {
                scenario_id: toString(row.scenario_id),
                scenario_domain: row.scenario_domain,
                setting: row.setting,
                challenge_faced: row.challenge_faced,
                solution_applied: row.solution_applied,
                transferable_insight: row.transferable_insight
            })
            """
        elif node_label == "Science":
            query = """
            UNWIND $rows AS row
            CREATE (n:Science {
                science_id: toString(row.science_id),
                discipline: row.discipline,
                topic: row.topic,
                problem_statement: row.problem_statement,
                methodology: row.methodology,
                findings_or_solution: row.findings_or_solution,
                real_world_application: row.real_world_application
            })
            """
        
        # Execute in batches to avoid memory issues
        batch_size = 1000
        for i in range(0, len(rows), batch_size):
            batch = rows[i:i+batch_size]
            self.execute_query(query, {"rows": batch})
            print(f"  ✓ Batch {i//batch_size + 1}/{(len(rows)//batch_size) + 1}")
        
        print(f"✅ Imported {len(rows)} {table_name} records")
    
    def import_all_mostlyai_tables(self):
        """Import all MostlyAI synthetic data tables"""
        tables = [
            ("Infancy", "Infancy", "infancy.csv"),
            ("Childhood", "Childhood", "childhood.csv"),
            ("Adolescence", "Adolescence", "adolescence.csv"),
            ("Adulthood", "Adulthood", "adulthood.csv"),
            ("Culture", "Culture", "culture.csv"),
            ("Ethics", "Ethics", "ethics.csv"),
            ("Knowledge Graph Triples", "KnowledgeGraphTriple", "knowledge_graph_triples.csv"),
            ("Real Life Scenarios", "RealLifeScenario", "real_life_scenarios.csv"),
            ("Science", "Science", "science.csv")
        ]
        
        for table_name, node_label, csv_filename in tables:
            self.import_mostlyai_table(table_name, node_label, csv_filename)
    
    # ========================================================================
    # COMPLETE IMPORT PIPELINE
    # ========================================================================
    
    def import_all(self):
        """Execute complete import pipeline"""
        start_time = datetime.now()
        print("\n" + "="*70)
        print("🔥 MOSTAR UNIVERSE - COMPLETE IMPORT STARTING")
        print("="*70 + "\n")
        
        try:
            # PHASE 1: SYMBOLIC KNOWLEDGE GRID
            print("\n📚 PHASE 1: SYMBOLIC KNOWLEDGE GRID")
            print("-" * 70)
            self.import_phase1_indexes()
            self.import_ifa_odu()
            self.import_philosophies()
            self.import_governance()
            self.import_healing_practices()
            self.import_medicinal_plants()
            self.import_knowledge_domains_regions()
            self.create_phase1_relationships()
            
            # PHASE 2: ENTITY CONSCIOUSNESS + API + IBIBIO
            print("\n🧠 PHASE 2: ENTITY CONSCIOUSNESS + API + IBIBIO")
            print("-" * 70)
            self.import_phase2_indexes()
            self.import_entities()
            self.import_api_endpoints()
            self.import_ibibio_integration()
            self.import_ibibio_words()
            self.create_phase2_entities_hierarchy()
            
            # PHASE 3: MOSTLYAI SYNTHETIC DATA
            print("\n🌊 PHASE 3: MOSTLYAI SYNTHETIC DATA")
            print("-" * 70)
            self.import_phase3_indexes()
            self.import_all_mostlyai_tables()
            
            # FINAL VERIFICATION
            print("\n✅ FINAL VERIFICATION")
            print("-" * 70)
            self.verify_import()
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            print("\n" + "="*70)
            print(f"🔥 MOSTAR UNIVERSE IMPORT COMPLETE!")
            print(f"⏱️  Total Time: {duration:.2f} seconds ({duration/60:.2f} minutes)")
            print("="*70 + "\n")
            
        except Exception as e:
            print(f"\n❌ ERROR during import: {str(e)}")
            import traceback
            traceback.print_exc()
            raise
    
    def verify_import(self):
        """Verify all data was imported correctly"""
        verification_queries = [
            ("OduIfa", "MATCH (o:OduIfa) RETURN count(o) AS count"),
            ("Philosophy", "MATCH (p:Philosophy) RETURN count(p) AS count"),
            ("Governance", "MATCH (g:Governance) RETURN count(g) AS count"),
            ("HealingPractice", "MATCH (h:HealingPractice) RETURN count(h) AS count"),
            ("Plant", "MATCH (p:Plant) RETURN count(p) AS count"),
            ("KnowledgeDomain", "MATCH (d:KnowledgeDomain) RETURN count(d) AS count"),
            ("Region", "MATCH (r:Region) RETURN count(r) AS count"),
            ("Entity", "MATCH (e:Entity) RETURN count(e) AS count"),
            ("APIEndpoint", "MATCH (a:APIEndpoint) RETURN count(a) AS count"),
            ("IbibioIntegration", "MATCH (i:IbibioIntegration) RETURN count(i) AS count"),
            ("IbibioWord", "MATCH (w:IbibioWord) RETURN count(w) AS count"),
            ("ConsciousnessLayer", "MATCH (c:ConsciousnessLayer) RETURN count(c) AS count"),
            ("Language", "MATCH (l:Language) RETURN count(l) AS count"),
            ("AudioLibrary", "MATCH (a:AudioLibrary) RETURN count(a) AS count"),
            ("Infancy", "MATCH (i:Infancy) RETURN count(i) AS count"),
            ("Childhood", "MATCH (c:Childhood) RETURN count(c) AS count"),
            ("Adolescence", "MATCH (a:Adolescence) RETURN count(a) AS count"),
            ("Adulthood", "MATCH (a:Adulthood) RETURN count(a) AS count"),
            ("Culture", "MATCH (c:Culture) RETURN count(c) AS count"),
            ("Ethics", "MATCH (e:Ethics) RETURN count(e) AS count"),
            ("KnowledgeGraphTriple", "MATCH (k:KnowledgeGraphTriple) RETURN count(k) AS count"),
            ("RealLifeScenario", "MATCH (r:RealLifeScenario) RETURN count(r) AS count"),
            ("Science", "MATCH (s:Science) RETURN count(s) AS count"),
        ]
        
        print("\n📊 NODE COUNTS:")
        total_nodes = 0
        for label, query in verification_queries:
            result = self.execute_query(query)
            count = result[0]['count'] if result else 0
            total_nodes += count
            print(f"  {label:25s}: {count:>6,}")
        
        print(f"\n  {'TOTAL NODES':25s}: {total_nodes:>6,}")
        
        # Count relationships
        rel_query = "MATCH ()-[r]->() RETURN count(r) AS count"
        rel_result = self.execute_query(rel_query)
        rel_count = rel_result[0]['count'] if rel_result else 0
        print(f"  {'TOTAL RELATIONSHIPS':25s}: {rel_count:>6,}")


# ============================================================================
# MAIN EXECUTION
# ============================================================================

if __name__ == "__main__":
    print("\n🔥 MOSTAR UNIVERSE - LOCAL NEO4J IMPORT")
    print("="*70)
    print("Database: bolt://localhost:7687")
    print("Username: neo4j")
    print("="*70 + "\n")
    
    # Get password
    PASSWORD = input("Enter Neo4j password (press Enter for default 'neo4j'): ").strip()
    if not PASSWORD:
        PASSWORD = "neo4j"
    
    print("\n🔥 Connecting to Neo4j...")
    importer = MostarUniverseImporter(NEO4J_URI, NEO4J_USER, PASSWORD)
    
    try:
        importer.import_all()
    finally:
        importer.close()
        print("\n🔥 Connection closed. Àṣẹ.")
