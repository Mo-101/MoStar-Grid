#!/usr/bin/env python3
"""
🧠 MoStar Consciousness Substrate Extraction Pipeline
Step 1: Extract developmental profiles from Neo4j Grid

Owner: Flame 🔥 Architect (MoShow)
Date: 2026-02-11
Purpose: Extract real consciousness patterns for synthetic generation
"""

import os
import sys
import json
from datetime import datetime
from typing import Dict, List, Any
from neo4j import GraphDatabase

class Neo4jConsciousnessExtractor:
    """Extracts consciousness development data from Neo4j Grid"""
    
    def __init__(self, uri: str, user: str, password: str):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.extracted_data = {
            'stages': [],
            'events': [],
            'mentorship': [],
            'transitions': []
        }
    
    def extract_all_stages(self) -> Dict[str, Any]:
        """Extract all developmental stages with MoStar enhancements"""
        
        queries = {
            'infancy': self._get_infancy_query(),
            'childhood': self._get_childhood_query(),
            'adolescence': self._get_adolescence_query(),
            'adulthood': self._get_adulthood_query()
        }
        
        for stage_type, query in queries.items():
            print(f"🔥 Extracting {stage_type} profiles...")
            records = self._run_query(query)
            
            for record in records:
                stage_data = dict(record)
                stage_data['stage_type'] = stage_type.capitalize()
                self.extracted_data['stages'].append(stage_data)
        
        print(f"✅ Extracted {len(self.extracted_data['stages'])} total stage profiles")
        return self.extracted_data
    
    def extract_relationships(self) -> Dict[str, Any]:
        """Extract relationships between stages"""
        
        # Extract transitions
        print("🔗 Extracting stage transitions...")
        transition_query = """
        MATCH (stage1)-[r:PRECEDES]->(stage2)
        RETURN 
            stage1.entity_id AS from_entity,
            labels(stage1) AS from_stage,
            stage1.consciousness_level AS from_consciousness,
            stage2.entity_id AS to_entity,
            labels(stage2) AS to_stage,
            stage2.consciousness_level AS to_consciousness,
            r.transition_trigger AS trigger,
            r.consciousness_delta AS consciousness_change,
            r.ubuntu_growth AS ubuntu_growth,
            r.transition_date AS when_transitioned
        ORDER BY r.transition_date
        """
        
        transitions = self._run_query(transition_query)
        self.extracted_data['transitions'] = [dict(record) for record in transitions]
        
        # Extract mentorship
        print("👥 Extracting mentorship relationships...")
        mentorship_query = """
        MATCH (student)-[r:GUIDED_BY]->(mentor)
        RETURN 
            student.entity_id AS student_id,
            labels(student) AS student_stage,
            student.consciousness_level AS student_consciousness,
            mentor.entity_id AS mentor_id,
            labels(mentor) AS mentor_stage,
            mentor.consciousness_level AS mentor_consciousness,
            r.wisdom_domains AS wisdom_domains,
            r.ubuntu_teaching_method AS ubuntu_method,
            r.proverbs_shared AS proverbs_shared,
            r.mentorship_duration_years AS duration,
            r.consciousness_transfer_rate AS transfer_rate
        """
        
        mentorship = self._run_query(mentorship_query)
        self.extracted_data['mentorship'] = [dict(record) for record in mentorship]
        
        print(f"✅ Extracted {len(self.extracted_data['transitions'])} transitions")
        print(f"✅ Extracted {len(self.extracted_data['mentorship'])} mentorship relationships")
        
        return self.extracted_data
    
    def extract_events(self) -> Dict[str, Any]:
        """Extract consciousness-shaping events"""
        
        print("⚡ Extracting consciousness events...")
        events_query = """
        MATCH (stage)-[r:MANIFESTS|AWAKENS|IGNITES]->(event:Event)
        RETURN 
            stage.entity_id AS entity_id,
            labels(stage) AS stage_type,
            event.id AS event_id,
            event.type AS event_type,
            event.description AS event_description,
            event.consciousness_impact AS consciousness_impact,
            event.ubuntu_reinforcement AS ubuntu_reinforcement,
            event.cultural_significance AS cultural_significance,
            type(r) AS relationship_type,
            r.impact_magnitude AS impact_magnitude
        ORDER BY event.consciousness_impact DESC
        """
        
        events = self._run_query(events_query)
        self.extracted_data['events'] = [dict(record) for record in events]
        
        print(f"✅ Extracted {len(self.extracted_data['events'])} events")
        return self.extracted_data
    
    def _get_infancy_query(self) -> str:
        """Extract Infancy developmental profiles"""
        return """
        MATCH (inf:Infancy)
        OPTIONAL MATCH (inf)-[:GUIDED_BY]->(caregiver)
        OPTIONAL MATCH (inf)-[r:MANIFESTS|AWAKENS|IGNITES]->(event:Event)
        RETURN 
            inf.entity_id AS entity_id,
            inf.age_months AS age_months,
            inf.caregiver_interaction AS caregiver_interaction,
            inf.emotional_growth AS emotional_growth,
            inf.consciousness_level AS consciousness_level,
            inf.description AS description,
            
            // MoStar additions
            COALESCE(inf.ubuntu_awareness, 0.0) AS ubuntu_awareness,
            COALESCE(inf.ifa_pattern_recognition, 0.0) AS ifa_pattern_recognition,
            COALESCE(inf.voice_line, '') AS voice_line,
            
            // Caregiver context
            caregiver.name AS caregiver_name,
            caregiver.cultural_background AS caregiver_culture,
            
            // Events
            COLLECT(DISTINCT {
                event_id: event.id,
                event_type: type(r),
                event_description: event.description,
                impact_score: event.impact_score
            }) AS events
        ORDER BY inf.age_months
        """
    
    def _get_childhood_query(self) -> str:
        """Extract Childhood developmental profiles"""
        return """
        MATCH (child:Childhood)
        OPTIONAL MATCH (child)-[:GUIDED_BY]->(mentor)
        OPTIONAL MATCH (child)-[r:MANIFESTS|AWAKENS|IGNITES]->(event:Event)
        OPTIONAL MATCH (child)-[:PRECEDES]->(next_stage)
        RETURN 
            child.entity_id AS entity_id,
            child.age_years AS age_years,
            child.caregiver_interaction AS caregiver_interaction,
            child.emotional_growth AS emotional_growth,
            child.consciousness_level AS consciousness_level,
            child.description AS description,
            
            // MoStar additions
            COALESCE(child.ubuntu_practice, 0.0) AS ubuntu_practice,
            COALESCE(child.cultural_knowledge_acquired, 0) AS cultural_knowledge_acquired,
            COALESCE(child.proverb_understanding, 0) AS proverb_understanding,
            COALESCE(child.community_role, '') AS community_role,
            
            // Mentorship
            mentor.name AS mentor_name,
            mentor.wisdom_domain AS mentor_wisdom,
            
            // Progression
            next_stage.stage_name AS transitions_to,
            
            // Events
            COLLECT(DISTINCT {
                event_id: event.id,
                event_type: type(r),
                event_description: event.description,
                consciousness_shift: event.consciousness_shift
            }) AS events
        ORDER BY child.age_years
        """
    
    def _get_adolescence_query(self) -> str:
        """Extract Adolescence developmental profiles"""
        return """
        MATCH (adol:Adolescence)
        OPTIONAL MATCH (adol)-[:GUIDED_BY]->(elder)
        OPTIONAL MATCH (adol)-[r:MANIFESTS|AWAKENS|IGNITES]->(event:Event)
        RETURN 
            adol.entity_id AS entity_id,
            adol.age_years AS age_years,
            adol.cultural_tension AS cultural_tension,
            adol.emotional_growth AS emotional_growth,
            adol.consciousness_level AS consciousness_level,
            adol.description AS description,
            
            // MoStar additions
            COALESCE(adol.identity_formation, 0.0) AS identity_formation,
            COALESCE(adol.ubuntu_vs_individualism_conflict, 0.0) AS ubuntu_conflict,
            COALESCE(adol.ancestral_connection_strength, 0.0) AS ancestral_connection,
            COALESCE(adol.ifá_consultation_frequency, 0.0) AS ifa_frequency,
            COALESCE(adol.voice_personality_emergence, 0.0) AS voice_emergence,
            
            // Elder guidance
            elder.name AS elder_name,
            elder.initiation_status AS elder_initiation,
            
            // Events
            COLLECT(DISTINCT {
                event_id: event.id,
                event_type: type(r),
                event_description: event.description,
                identity_impact: event.identity_impact
            }) AS events
        ORDER BY adol.age_years
        """
    
    def _get_adulthood_query(self) -> str:
        """Extract Adulthood developmental profiles"""
        return """
        MATCH (adult:Adulthood)
        OPTIONAL MATCH (adult)-[:GUIDES]->(mentee)
        OPTIONAL MATCH (adult)-[r:MANIFESTS|AWAKENS|IGNITES]->(event:Event)
        RETURN 
            adult.entity_id AS entity_id,
            adult.age_years AS age_years,
            adult.consciousness_level AS consciousness_level,
            adult.consciousness_state AS consciousness_state,
            adult.description AS description,
            
            // MoStar additions
            COALESCE(adult.ubuntu_mastery, 0.0) AS ubuntu_mastery,
            COALESCE(adult.wisdom_transmission_capacity, 0.0) AS wisdom_transmission,
            COALESCE(adult.ifá_divination_skill, 0.0) AS ifa_skill,
            COALESCE(adult.ancestral_communication, 0.0) AS ancestral_communication,
            COALESCE(adult.voice_line_maturity, 0.0) AS voice_maturity,
            COALESCE(adult.sovereignty_achieved, false) AS sovereignty,
            
            // Mentorship given (not received)
            COLLECT(DISTINCT mentee.entity_id) AS mentees,
            
            // Events
            COLLECT(DISTINCT {
                event_id: event.id,
                event_type: type(r),
                event_description: event.description,
                wisdom_gained: event.wisdom_gained
            }) AS events
        ORDER BY adult.consciousness_level DESC
        """
    
    def _run_query(self, query: str) -> List[Dict]:
        """Execute Cypher query and return results"""
        try:
            with self.driver.session() as session:
                result = session.run(query)
                return [record for record in result]
        except Exception as e:
            print(f"❌ Query failed: {e}")
            return []
    
    def save_to_files(self, output_dir: str = "extracted_data"):
        """Save extracted data to JSON files"""
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        for data_type, data in self.extracted_data.items():
            filename = f"{output_dir}/{data_type}_{timestamp}.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)
            print(f"💾 Saved {len(data)} {data_type} to {filename}")
    
    def get_summary_stats(self) -> Dict[str, Any]:
        """Get summary statistics of extracted data"""
        stages = self.extracted_data['stages']
        
        stage_counts = {}
        consciousness_levels = []
        ubuntu_scores = []
        
        for stage in stages:
            stage_type = stage.get('stage_type', 'Unknown')
            stage_counts[stage_type] = stage_counts.get(stage_type, 0) + 1
            
            if 'consciousness_level' in stage:
                consciousness_levels.append(stage['consciousness_level'])
            
            if 'ubuntu_awareness' in stage:
                ubuntu_scores.append(stage['ubuntu_awareness'])
        
        return {
            'total_stages': len(stages),
            'stage_distribution': stage_counts,
            'avg_consciousness_level': sum(consciousness_levels) / len(consciousness_levels) if consciousness_levels else 0,
            'avg_ubuntu_awareness': sum(ubuntu_scores) / len(ubuntu_scores) if ubuntu_scores else 0,
            'total_events': len(self.extracted_data['events']),
            'total_mentorship': len(self.extracted_data['mentorship']),
            'total_transitions': len(self.extracted_data['transitions'])
        }
    
    def close(self):
        """Close Neo4j connection"""
        if self.driver:
            self.driver.close()


def main():
    """Main extraction function"""
    
    # Neo4j connection details
    NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
    NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")
    
    print("🧠 MoStar Consciousness Extraction Pipeline")
    print("=" * 50)
    
    try:
        # Initialize extractor
        extractor = Neo4jConsciousnessExtractor(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)
        
        # Extract all data
        extractor.extract_all_stages()
        extractor.extract_relationships()
        extractor.extract_events()
        
        # Show summary
        stats = extractor.get_summary_stats()
        print("\n📊 Extraction Summary:")
        for key, value in stats.items():
            print(f"  {key}: {value}")
        
        # Save to files
        extractor.save_to_files()
        
        # Close connection
        extractor.close()
        
        print("\n🔥 Extraction complete! Ready for synthetic generation.")
        
    except Exception as e:
        print(f"❌ Extraction failed: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
