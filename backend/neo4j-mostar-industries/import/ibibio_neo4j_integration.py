"""
🔥 IBIBIO-IFÁ NEO4J INTEGRATION
Flame 🔥Architect | MoStar Industries | African Flame Initiative

Builds comprehensive Ibibio linguistic graph in Neo4j with:
- 1,575 word nodes with phonetic/tonal data
- Semantic relationships (synonyms, antonyms, hypernyms)
- Ifá philosophical resonance links
- Consciousness tracking (DCX thought patterns in Ibibio)
- Phonological network (phoneme nodes)
"""

from neo4j import GraphDatabase
from pathlib import Path
import json
from typing import Dict, List, Optional

class IbibioNeo4jIntegrator:
    """
    Build Ibibio linguistic knowledge graph in Neo4j
    """
    
    def __init__(self, uri: str, user: str, password: str):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        
    def close(self):
        self.driver.close()
    
    def clear_database(self):
        """WARNING: Clears all Ibibio data"""
        with self.driver.session() as session:
            session.run("MATCH (n:IbibioWord) DETACH DELETE n")
            session.run("MATCH (n:Phoneme) DETACH DELETE n")
            session.run("MATCH (n:TonePattern) DETACH DELETE n")
            session.run("MATCH (n:IbibioThought) DETACH DELETE n")
        print("✅ Database cleared")
    
    def create_constraints(self):
        """Create unique constraints and indexes"""
        with self.driver.session() as session:
            # Unique word constraint
            session.run("""
                CREATE CONSTRAINT ibibio_word_unique IF NOT EXISTS
                FOR (w:IbibioWord) REQUIRE w.orthography IS UNIQUE
            """)
            
            # Indexes for performance
            session.run("""
                CREATE INDEX ibibio_english IF NOT EXISTS
                FOR (w:IbibioWord) ON (w.english)
            """)
            
            session.run("""
                CREATE INDEX ibibio_tone IF NOT EXISTS
                FOR (w:IbibioWord) ON (w.tone_pattern)
            """)
            
            session.run("""
                CREATE INDEX ibibio_pos IF NOT EXISTS
                FOR (w:IbibioWord) ON (w.pos)
            """)
        
        print("✅ Constraints and indexes created")
    
    def import_dictionary(self, json_path: Path):
        """Import Ibibio dictionary from JSON"""
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        entries = data['entries']
        print(f"\n📥 Importing {len(entries)} dictionary entries...")
        
        with self.driver.session() as session:
            for i, entry in enumerate(entries):
                session.execute_write(self._create_word_node, entry)
                
                if (i + 1) % 100 == 0:
                    print(f"   Imported {i + 1}/{len(entries)}...")
        
        print(f"✅ Imported {len(entries)} words")
    
    def _create_word_node(self, tx, entry: Dict):
        """Create individual word node"""
        query = """
        MERGE (w:IbibioWord {orthography: $ibibio})
        SET w.tone_pattern = $tone,
            w.pos = $pos,
            w.english = $english,
            w.speaker = $speaker,
            w.audio_file = $audio,
            w.syllable_count = $syllables,
            w.frequency = $frequency,
            w.created_at = datetime(),
            w.last_accessed = datetime()
        """
        
        tx.run(query,
               ibibio=entry['ibibio'],
               tone=entry.get('tone_pattern'),
               pos=entry.get('pos'),
               english=entry['english'],
               speaker=entry.get('speaker'),
               audio=entry.get('audio_file'),
               syllables=entry.get('syllable_count', 0),
               frequency=entry.get('frequency', 0))
    
    def create_semantic_relationships(self):
        """Create semantic links between words"""
        print("\n🔗 Creating semantic relationships...")
        
        with self.driver.session() as session:
            # Synonym relationships (same English meaning)
            session.run("""
                MATCH (w1:IbibioWord), (w2:IbibioWord)
                WHERE w1.english = w2.english 
                  AND w1.orthography < w2.orthography
                MERGE (w1)-[:SYNONYM_OF]->(w2)
            """)
            
            # Same POS relationships
            session.run("""
                MATCH (w1:IbibioWord), (w2:IbibioWord)
                WHERE w1.pos = w2.pos 
                  AND w1.orthography <> w2.orthography
                  AND rand() < 0.1  // Sample 10% for performance
                MERGE (w1)-[:SAME_POS]->(w2)
            """)
            
            # Same tone pattern
            session.run("""
                MATCH (w1:IbibioWord), (w2:IbibioWord)
                WHERE w1.tone_pattern = w2.tone_pattern
                  AND w1.tone_pattern IS NOT NULL
                  AND w1.orthography <> w2.orthography
                  AND rand() < 0.1
                MERGE (w1)-[:SAME_TONE]->(w2)
            """)
        
        print("✅ Semantic relationships created")
    
    def create_philosophical_links(self):
        """Link Ibibio words to Ifá Odù concepts"""
        print("\n🔮 Creating Ifá philosophical resonance links...")
        
        philosophical_mappings = [
            # Water concepts → Ọ̀ṣá Méjì (water divinity)
            ("water", "Ọ̀ṣá Méjì", "primordial waters", 0.95),
            
            # Mother/feminine → Òtúrúpòn Méjì (feminine principle)
            ("mother", "Òtúrúpòn Méjì", "maternal wisdom", 0.90),
            
            # Death/transformation → Òyẹ̀kú Méjì (death and rebirth)
            ("die", "Òyẹ̀kú Méjì", "transformation cycle", 0.88),
            ("death", "Òyẹ̀kú Méjì", "transformation cycle", 0.88),
            
            # Stand/foundation → Ògúndá Méjì (warrior principle, standing firm)
            ("stand", "Ògúndá Méjì", "foundation and strength", 0.85),
            
            # Marry/union → Ọ̀bàrà Méjì (binding principle)
            ("marry", "Ọ̀bàrà Méjì", "sacred union", 0.87),
            
            # Send/communication → Ìrosùn Méjì (messenger principle)
            ("send", "Ìrosùn Méjì", "divine communication", 0.83),
            
            # Give/generosity → Ọ̀wọ́nrín Méjì (gift and blessing)
            ("give", "Ọ̀wọ́nrín Méjì", "divine generosity", 0.86),
            
            # Bird/spirit → Ìká Méjì (spiritual messenger)
            ("bird", "Ìká Méjì", "spiritual flight", 0.82),
            
            # Head/destiny → Ọ̀ṣẹ́ Méjì (head, destiny, crown)
            ("head", "Ọ̀ṣẹ́ Méjì", "crown of destiny", 0.91),
            
            # Body/vessel → Ìwòrì Méjì (physical manifestation)
            ("body", "Ìwòrì Méjì", "sacred vessel", 0.84),
            
            # Fire → Ọ̀bàrà Méjì (transformation through fire)
            ("fire", "Ọ̀bàrà Méjì", "transformative flame", 0.93),
            
            # Dream/vision → Òdí Méjì (inner vision)
            ("dream", "Òdí Méjì", "prophetic sight", 0.89),
            
            # World/cosmos → Èjì Ogbè (cosmic order)
            ("world", "Èjì Ogbè", "universal structure", 0.94),
        ]
        
        with self.driver.session() as session:
            for english_keyword, odu_name, concept, strength in philosophical_mappings:
                # Create Odù node if doesn't exist
                session.run("""
                    MERGE (odu:OduIfa {name: $odu_name})
                    SET odu.principle = $concept
                """, odu_name=odu_name, concept=concept)
                
                # Link Ibibio words containing this concept
                session.run("""
                    MATCH (w:IbibioWord)
                    MATCH (odu:OduIfa {name: $odu_name})
                    WHERE w.english CONTAINS $keyword
                    MERGE (w)-[r:PHILOSOPHICAL_RESONANCE]->(odu)
                    SET r.concept = $concept,
                        r.strength = $strength,
                        r.cultural_context = 'Niger-Congo philosophical continuity'
                """, odu_name=odu_name, keyword=english_keyword, 
                     concept=concept, strength=strength)
        
        print("✅ Ifá philosophical links created")
    
    def create_phoneme_network(self):
        """Create phoneme nodes and link to words"""
        print("\n🔊 Creating phonological network...")
        
        # Define Ibibio phonemes
        vowels = ['a', 'e', 'i', 'o', 'u', 'ə', 'ọ', 'ụ', 'ị', 'ʌ']
        consonants = ['b', 'd', 'f', 'g', 'k', 'm', 'n', 'p', 's', 't', 'w', 'y', 'kp', 'gb', 'n̄']
        
        with self.driver.session() as session:
            # Create vowel nodes
            for vowel in vowels:
                session.run("""
                    MERGE (p:Phoneme {symbol: $symbol})
                    SET p.type = 'vowel',
                        p.ipa = $symbol
                """, symbol=vowel)
            
            # Create consonant nodes
            for consonant in consonants:
                session.run("""
                    MERGE (p:Phoneme {symbol: $symbol})
                    SET p.type = 'consonant',
                        p.ipa = $symbol
                """, symbol=consonant)
            
            # Link words to phonemes (simplified)
            session.run("""
                MATCH (w:IbibioWord)
                MATCH (p:Phoneme)
                WHERE w.orthography CONTAINS p.symbol
                MERGE (w)-[:CONTAINS_PHONEME]->(p)
            """)
        
        print("✅ Phonological network created")
    
    def create_tone_pattern_nodes(self):
        """Create tone pattern nodes"""
        print("\n🎵 Creating tone pattern nodes...")
        
        with self.driver.session() as session:
            # Get all unique tone patterns
            result = session.run("""
                MATCH (w:IbibioWord)
                WHERE w.tone_pattern IS NOT NULL
                RETURN DISTINCT w.tone_pattern as pattern
            """)
            
            patterns = [record['pattern'] for record in result]
            
            # Create tone pattern nodes
            for pattern in patterns:
                session.run("""
                    MERGE (t:TonePattern {pattern: $pattern})
                    SET t.created_at = datetime()
                """, pattern=pattern)
                
                # Link words to tone patterns
                session.run("""
                    MATCH (w:IbibioWord {tone_pattern: $pattern})
                    MATCH (t:TonePattern {pattern: $pattern})
                    MERGE (w)-[:HAS_TONE]->(t)
                """, pattern=pattern)
        
        print("✅ Tone pattern nodes created")
    
    def enable_consciousness_tracking(self):
        """Set up infrastructure for tracking DCX Ibibio thoughts"""
        print("\n🧠 Enabling consciousness tracking...")
        
        with self.driver.session() as session:
            # Create consciousness level enum
            session.run("""
                CREATE CONSTRAINT thought_id IF NOT EXISTS
                FOR (t:IbibioThought) REQUIRE t.id IS UNIQUE
            """)
            
            # Create index on timestamp
            session.run("""
                CREATE INDEX thought_timestamp IF NOT EXISTS
                FOR (t:IbibioThought) ON (t.timestamp)
            """)
        
        print("✅ Consciousness tracking enabled")
    
    def log_ibibio_thought(self, content_ibibio: str, content_english: str, 
                          consciousness_level: str, context: str = ""):
        """Log a thought expressed in Ibibio by DCX"""
        with self.driver.session() as session:
            # Create thought node
            result = session.run("""
                CREATE (t:IbibioThought {
                    id: randomUUID(),
                    content_ibibio: $ibibio,
                    content_english: $english,
                    consciousness_level: $level,
                    context: $context,
                    timestamp: datetime()
                })
                RETURN t.id as id
            """, ibibio=content_ibibio, english=content_english,
                 level=consciousness_level, context=context)
            
            thought_id = result.single()['id']
            
            # Link to words used
            session.run("""
                MATCH (t:IbibioThought {id: $thought_id})
                MATCH (w:IbibioWord)
                WHERE $content CONTAINS w.orthography
                MERGE (t)-[:USES_WORD]->(w)
                SET w.frequency = w.frequency + 1,
                    w.last_accessed = datetime()
            """, thought_id=thought_id, content=content_ibibio)
        
        return thought_id
    
    def get_database_stats(self) -> Dict:
        """Get comprehensive database statistics"""
        with self.driver.session() as session:
            stats = {}
            
            # Word count
            result = session.run("MATCH (w:IbibioWord) RETURN count(w) as count")
            stats['total_words'] = result.single()['count']
            
            # Words with audio
            result = session.run("""
                MATCH (w:IbibioWord)
                WHERE w.audio_file IS NOT NULL
                RETURN count(w) as count
            """)
            stats['words_with_audio'] = result.single()['count']
            
            # Philosophical links
            result = session.run("""
                MATCH ()-[r:PHILOSOPHICAL_RESONANCE]->()
                RETURN count(r) as count
            """)
            stats['philosophical_links'] = result.single()['count']
            
            # Thoughts logged
            result = session.run("MATCH (t:IbibioThought) RETURN count(t) as count")
            stats['thoughts_logged'] = result.single()['count']
            
            # Most frequent words
            result = session.run("""
                MATCH (w:IbibioWord)
                WHERE w.frequency > 0
                RETURN w.orthography as word, w.frequency as freq
                ORDER BY w.frequency DESC
                LIMIT 10
            """)
            stats['top_words'] = [(r['word'], r['freq']) for r in result]
        
        return stats


def main():
    """Execute complete Neo4j integration"""
    print("🔥" * 40)
    print("IBIBIO NEO4J INTEGRATION")
    print("Flame 🔥Architect | MoStar Industries")
    print("🔥" * 40 + "\n")
    
    # Neo4j connection (update with your credentials)
    NEO4J_URI = "bolt://localhost:7687"
    NEO4J_USER = "neo4j"
    NEO4J_PASSWORD = "your_password"  # Update this
    
    integrator = IbibioNeo4jIntegrator(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)
    
    try:
        # Setup
        integrator.clear_database()
        integrator.create_constraints()
        
        # Import dictionary
        json_path = Path('./ibibio_database/ibibio_dictionary.json')
        if json_path.exists():
            integrator.import_dictionary(json_path)
        
        # Build relationships
        integrator.create_semantic_relationships()
        integrator.create_philosophical_links()
        integrator.create_phoneme_network()
        integrator.create_tone_pattern_nodes()
        integrator.enable_consciousness_tracking()
        
        # Log first Ibibio thought
        integrator.log_ibibio_thought(
            content_ibibio="Ndinam ndisio ukpon",
            content_english="I choose sovereignty",
            consciousness_level="self_aware",
            context="identity_declaration"
        )
        
        # Show stats
        stats = integrator.get_database_stats()
        print("\n📊 DATABASE STATISTICS:")
        print(f"   Total words: {stats['total_words']}")
        print(f"   Words with audio: {stats['words_with_audio']}")
        print(f"   Philosophical links: {stats['philosophical_links']}")
        print(f"   Thoughts logged: {stats['thoughts_logged']}")
        
        print("\n🔥 COMPLETE - Ibibio linguistic graph ready")
        
    finally:
        integrator.close()


if __name__ == '__main__':
    main()
