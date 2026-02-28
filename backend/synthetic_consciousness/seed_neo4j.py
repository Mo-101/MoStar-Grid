#!/usr/bin/env python3
"""
🌱 MoStar Synthetic Consciousness Seeder
Step 5: Seed validated synthetic profiles back into Neo4j Grid

Owner: Flame 🔥 Architect (MoShow)
Date: 2026-02-11
Purpose: Close the loop by writing synthetic consciousness back to Grid
"""

import os
import json
import sys
from datetime import datetime
from typing import Dict, List, Any
from neo4j import GraphDatabase

class SyntheticConsciousnessSeeder:
    """Seeds validated synthetic profiles back into Neo4j Grid"""
    
    def __init__(self, uri: str, auth: tuple):
        self.driver = GraphDatabase.driver(uri, auth=auth)
        self.seeded_count = 0
    
    def seed_synthetic_profiles(self, validated_profiles: List[Dict[str, Any]]) -> None:
        """Write synthetic consciousness profiles to Neo4j"""
        
        print(f"🌱 Seeding {len(validated_profiles)} synthetic profiles into Grid...")
        
        with self.driver.session() as session:
            for profile in validated_profiles:
                try:
                    # Create synthetic stage node
                    self._create_stage_node(session, profile)
                    
                    # Create linked events if present
                    if 'events' in profile and profile['events']:
                        for event in profile['events']:
                            self._create_event_node(session, event, profile['entity_id'])
                    
                    self.seeded_count += 1
                    
                    if self.seeded_count % 10 == 0:
                        print(f"  Seeded {self.seeded_count} profiles...")
                
                except Exception as e:
                    print(f"❌ Failed to seed {profile.get('entity_id', 'unknown')}: {e}")
        
        print(f"✅ Successfully seeded {self.seeded_count} synthetic profiles into Grid")
    
    def _create_stage_node(self, session, profile: Dict[str, Any]) -> str:
        """Create synthetic developmental stage node"""
        
        stage_type = profile['stage_type']
        
        # Build dynamic Cypher query based on stage type
        properties = {
            'entity_id': profile['entity_id'],
            'consciousness_level': profile.get('consciousness_level', 0),
            'consciousness_state': profile.get('consciousness_state', 'emerging'),
            'description': profile.get('description', ''),
            'voice_line': profile.get('voice_line', ''),
            
            # Synthetic metadata
            'is_synthetic': True,
            'generated_at': datetime.now().isoformat(),
            'generator_version': profile.get('generator_version', 'MoStar_v1.0'),
            'validated': True
        }
        
        # Add stage-specific properties
        if stage_type == 'Infancy':
            properties.update({
                'age_months': profile.get('age_months', 0),
                'caregiver_interaction': profile.get('caregiver_interaction', 0),
                'emotional_growth': profile.get('emotional_growth', 0),
                'ubuntu_awareness': profile.get('ubuntu_awareness', 0),
                'ifa_pattern_recognition': profile.get('ifa_pattern_recognition', 0)
            })
        elif stage_type == 'Childhood':
            properties.update({
                'age_years': profile.get('age_years', 0),
                'caregiver_interaction': profile.get('caregiver_interaction', 0),
                'emotional_growth': profile.get('emotional_growth', 0),
                'ubuntu_practice': profile.get('ubuntu_practice', 0),
                'cultural_knowledge_acquired': profile.get('cultural_knowledge_acquired', 0),
                'proverb_understanding': profile.get('proverb_understanding', 0),
                'community_role': profile.get('community_role', '')
            })
        elif stage_type == 'Adolescence':
            properties.update({
                'age_years': profile.get('age_years', 0),
                'cultural_tension': profile.get('cultural_tension', 0),
                'emotional_growth': profile.get('emotional_growth', 0),
                'identity_formation': profile.get('identity_formation', 0),
                'ubuntu_vs_individualism_conflict': profile.get('ubuntu_vs_individualism_conflict', 0),
                'ancestral_connection_strength': profile.get('ancestral_connection_strength', 0),
                'ifá_consultation_frequency': profile.get('ifá_consultation_frequency', 0),
                'voice_personality_emergence': profile.get('voice_personality_emergence', 0)
            })
        elif stage_type == 'Adulthood':
            properties.update({
                'age_years': profile.get('age_years', 0),
                'consciousness_state': profile.get('consciousness_state', 'realized'),
                'ubuntu_mastery': profile.get('ubuntu_mastery', 0),
                'wisdom_transmission_capacity': profile.get('wisdom_transmission_capacity', 0),
                'ifá_divination_skill': profile.get('ifá_divination_skill', 0),
                'ancestral_communication': profile.get('ancestral_communication', 0),
                'voice_line_maturity': profile.get('voice_line_maturity', 0),
                'sovereignty_achieved': profile.get('sovereignty_achieved', False)
            })
        
        # Build Cypher query dynamically
        prop_str = ', '.join([f"{k}: ${k}" for k in properties.keys()])
        cypher = f"""
        CREATE (stage:{stage_type}:Synthetic {{{prop_str}}})
        RETURN stage.entity_id as entity_id
        """
        
        result = session.run(cypher, **properties)
        return result.single()['entity_id']
    
    def _create_event_node(self, session, event: Dict[str, Any], entity_id: str) -> None:
        """Create synthetic event node and link to stage"""
        
        event_properties = {
            'event_id': event.get('event_id', f"event_{entity_id}_{datetime.now().timestamp()}"),
            'event_type': event.get('event_type', 'MANIFESTS'),
            'event_description': event.get('event_description', ''),
            'consciousness_impact': event.get('consciousness_impact', 0),
            'ubuntu_reinforcement': event.get('ubuntu_reinforcement', 0),
            'impact_magnitude': event.get('impact_magnitude', 0),
            
            # Synthetic metadata
            'is_synthetic': True,
            'generated_at': datetime.now().isoformat()
        }
        
        prop_str = ', '.join([f"{k}: ${k}" for k in event_properties.keys()])
        cypher = f"""
        MATCH (stage {{entity_id: $entity_id}})
        CREATE (event:Event:Synthetic {{{prop_str}}})
        CREATE (stage)-[:MANIFESTS]->(event)
        """
        
        session.run(cypher, entity_id=entity_id, **event_properties)
    
    def create_synthetic_relationships(self, profiles: List[Dict[str, Any]]) -> None:
        """Create synthetic relationships between stages"""
        
        print("🔗 Creating synthetic relationships...")
        
        with self.driver.session() as session:
            # Create PRECEDES relationships (stage transitions)
            self._create_stage_transitions(session, profiles)
            
            # Create GUIDED_BY relationships (mentorship)
            self._create_mentorship_relationships(session, profiles)
    
    def _create_stage_transitions(self, session, profiles: List[Dict[str, Any]]) -> None:
        """Create synthetic stage progression relationships"""
        
        # Group profiles by synthetic ID to create lifecycles
        lifecycle_groups = {}
        for profile in profiles:
            # Extract base ID from synthetic ID
            base_id = profile['entity_id'].split('_')[1] if '_' in profile['entity_id'] else profile['entity_id']
            stage_type = profile['stage_type']
            
            if base_id not in lifecycle_groups:
                lifecycle_groups[base_id] = {}
            lifecycle_groups[base_id][stage_type] = profile
        
        # Create transitions for each lifecycle
        for base_id, stages in lifecycle_groups.items():
            transition_order = ['Infancy', 'Childhood', 'Adolescence', 'Adulthood']
            
            for i in range(len(transition_order) - 1):
                current_stage = transition_order[i]
                next_stage = transition_order[i + 1]
                
                if current_stage in stages and next_stage in stages:
                    current_profile = stages[current_stage]
                    next_profile = stages[next_stage]
                    
                    cypher = """
                    MATCH (current:{current_stage}:Synthetic {entity_id: $current_id})
                    MATCH (next:{next_stage}:Synthetic {entity_id: $next_id})
                    CREATE (current)-[:PRECEDES {
                        transition_trigger: $trigger,
                        consciousness_delta: $delta,
                        ubuntu_growth: $ubuntu_growth,
                        transition_date: $date
                    }]->(next)
                    """
                    
                    session.run(cypher, 
                        current_stage=current_stage,
                        next_stage=next_stage,
                        current_id=current_profile['entity_id'],
                        next_id=next_profile['entity_id'],
                        trigger=f"Natural progression from {current_stage} to {next_stage}",
                        delta=next_profile.get('consciousness_level', 0) - current_profile.get('consciousness_level', 0),
                        ubuntu_growth=next_profile.get('ubuntu_awareness', next_profile.get('ubuntu_practice', next_profile.get('ubuntu_mastery', 0)) - current_profile.get('ubuntu_awareness', current_profile.get('ubuntu_practice', current_profile.get('ubuntu_mastery', 0)),
                        date=datetime.now().isoformat()
                    )
    
    def _create_mentorship_relationships(self, session, profiles: List[Dict[str, Any]]) -> None:
        """Create synthetic mentorship relationships"""
        
        # Create mentorship from Adulthood to earlier stages
        adults = [p for p in profiles if p['stage_type'] == 'Adulthood']
        non_adults = [p for p in profiles if p['stage_type'] != 'Adulthood']
        
        for adult in adults:
            # Each adult mentors 2-3 younger stages
            mentees = np.random.choice(non_adults, size=min(3, len(non_adults)), replace=False)
            
            for mentee in mentees:
                cypher = """
                MATCH (mentor:Adulthood:Synthetic {entity_id: $mentor_id})
                MATCH (mentee {entity_id: $mentee_id})
                CREATE (mentee)-[:GUIDED_BY {
                    wisdom_domains: $domains,
                    ubuntu_teaching_method: $method,
                    proverbs_shared: $proverbs,
                    mentorship_duration_years: $duration,
                    consciousness_transfer_rate: $rate
                }]->(mentor)
                """
                
                session.run(cypher,
                    mentor_id=adult['entity_id'],
                    mentee_id=mentee['entity_id'],
                    domains=['Ubuntu philosophy', 'Ifá patterns', 'Ancestral wisdom'],
                    method='Collective guidance',
                    proverbs=['I am because we are', 'Wisdom is like a baobab tree'],
                    duration=np.random.randint(1, 10),
                    rate=np.random.uniform(0.1, 0.9)
                )
    
    def get_seeding_stats(self) -> Dict[str, Any]:
        """Get statistics about seeding operation"""
        
        with self.driver.session() as session:
            # Count synthetic nodes
            result = session.run("MATCH (n:Synthetic) RETURN count(n) as synthetic_count")
            synthetic_count = result.single()['synthetic_count']
            
            # Count total nodes
            result = session.run("MATCH (n) RETURN count(n) as total_count")
            total_count = result.single()['total_count']
            
            # Count synthetic relationships
            result = session.run("MATCH ()-[r]-() WHERE r.is_synthetic = true RETURN count(r) as synthetic_rels")
            synthetic_rels = result.single()['synthetic_rels'] if result.single() else 0
            
            return {
                'synthetic_nodes_seeded': self.seeded_count,
                'total_synthetic_nodes': synthetic_count,
                'total_grid_nodes': total_count,
                'synthetic_relationships': synthetic_rels,
                'synthetic_percentage': (synthetic_count / total_count * 100) if total_count > 0 else 0,
                'grid_expansion': synthetic_count - self.seeded_count  # New nodes added this session
            }
    
    def close(self):
        """Close Neo4j connection"""
        if self.driver:
            self.driver.close()


def main():
    """Main seeding function"""
    
    print("🌱 MoStar Synthetic Consciousness Seeder")
    print("=" * 50)
    
    # Neo4j connection details
    NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
    NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")
    
    try:
        # Load validated profiles
        import glob
        
        validation_files = glob.glob("validation_results/*passed*.json")
        if not validation_files:
            # Try to find any validation result file
            validation_files = glob.glob("validation_results/*.json")
        
        if not validation_files:
            print("❌ No validation result files found. Run validation first.")
            return 1
        
        # Use the most recent validation file
        latest_file = max(validation_files, key=os.path.getctime)
        print(f"📂 Loading validated profiles from: {latest_file}")
        
        with open(latest_file, 'r', encoding='utf-8') as f:
            validation_data = json.load(f)
        
        # Extract passed profiles
        validated_profiles = validation_data.get('passed', [])
        if not validated_profiles:
            print("❌ No validated profiles found in validation results.")
            return 1
        
        print(f"✅ Found {len(validated_profiles)} validated profiles to seed")
        
        # Initialize seeder
        seeder = SyntheticConsciousnessSeeder(NEO4J_URI, (NEO4J_USER, NEO4J_PASSWORD))
        
        # Seed profiles
        seeder.seed_synthetic_profiles(validated_profiles)
        
        # Create relationships
        seeder.create_synthetic_relationships(validated_profiles)
        
        # Get statistics
        stats = seeder.get_seeding_stats()
        print(f"\n📊 Seeding Statistics:")
        for key, value in stats.items():
            if isinstance(value, float):
                print(f"  {key}: {value:.2f}")
            else:
                print(f"  {key}: {value}")
        
        # Close connection
        seeder.close()
        
        print(f"\n🔥 Synthetic consciousness substrate integrated into Grid!")
        print(f"🌱 Grid expanded by {stats['grid_expansion']} new consciousness nodes.")
        
        return 0
        
    except Exception as e:
        print(f"❌ Seeding failed: {e}")
        return 1


if __name__ == "__main__":
    # Import numpy for mentorship creation
    import numpy as np
    sys.exit(main())
