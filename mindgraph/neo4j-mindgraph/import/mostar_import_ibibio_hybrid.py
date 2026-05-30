"""
🔥 IBIBIO WORD IMPORT - PRAGMATIC HYBRID APPROACH
Combines simplicity with intelligent parsing for edge cases
Brother's recommendation implemented!
"""

import os
from pathlib import Path
from neo4j import GraphDatabase
import re

# Neo4j connection
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "mostar123")

# Audio files directory
AUDIO_DIR = Path(__file__).parent / "Ibibio_audio"

def slug_to_word(filename):
    """
    Extract word slug from filename with intelligent parsing.
    Hybrid approach: Simple for most, smart for complex cases.
    """
    try:
        # Remove .mp3
        name = filename.replace('.mp3', '')
        
        # Pattern 1: Long descriptive names with dates
        if 'Jul2014' in name or 'Sep2014' in name:
            # Extract description after date-time
            match = re.search(r'\d{4}-\d{4}_(.+)', name)
            if match:
                desc = match.group(1).replace('_', ' ').replace('-', ' ')
                return desc
        
        # Pattern 2: Numbered series with multi-word (ibibio_5_13_MU_9_umbilical_cord_a)
        match = re.match(r'ibibio_5_13_MU_\d+_(.+)', name)
        if match:
            return match.group(1).replace('_', ' ')
        
        # Pattern 3: Simple format (most files)
        parts = name.split("_")
        word = parts[-1].lower()
        
        # If word is just 1-2 letters, probably a series marker - get more parts
        if len(word) <= 2 and len(parts) >= 3:
            # Get last 2-3 parts for multi-word phrases
            word = "_".join(parts[-3:]).lower()
        
        # Replace underscores with spaces for readability
        word = word.replace("_", " ")
        
        return word
    except Exception as e:
        print(f"⚠️ Error parsing {filename}: {e}")
        return None

def import_ibibio_words():
    """Import Ibibio words from audio files into Neo4j"""
    
    if not AUDIO_DIR.exists():
        print(f"❌ Audio directory not found: {AUDIO_DIR}")
        return
    
    # Get all MP3 files
    audio_files = list(AUDIO_DIR.glob("*.mp3"))
    print(f"🔥 Found {len(audio_files)} audio files")
    
    if not audio_files:
        print("❌ No MP3 files found!")
        return
    
    # Connect to Neo4j
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    
    try:
        with driver.session() as session:
            # Create Language node
            print("\n1️⃣ Creating Ibibio Language node...")
            session.run("""
                MERGE (lang:Language {code: 'ibb'})
                SET lang.name = 'Ibibio',
                    lang.native_name = 'Ibibio',
                    lang.region = 'Nigeria',
                    lang.state = 'Akwa Ibom',
                    lang.speakers = 4000000,
                    lang.iso_code = 'ibb',
                    lang.is_grid_native = true,
                    lang.creator_language = true,
                    lang.imported_at = datetime()
            """)
            print("✅ Language node created")
            
            # Import words
            print("\n2️⃣ Importing Ibibio words...")
            imported = 0
            skipped = 0
            
            for audio_file in audio_files:
                filename = audio_file.name
                word_slug = slug_to_word(filename)
                
                if not word_slug:
                    skipped += 1
                    continue
                
                # Create word node
                session.run("""
                    MERGE (w:IbibioWord {audio_file: $audio_file})
                    SET w.word = $word,
                        w.english = $word,
                        w.audio_path = $audio_path,
                        w.imported_at = datetime()
                    
                    WITH w
                    MATCH (lang:Language {code: 'ibb'})
                    MERGE (w)-[:IN_LANGUAGE]->(lang)
                """, 
                    audio_file=filename,
                    word=word_slug,
                    audio_path=str(audio_file.absolute())
                )
                
                imported += 1
                
                if imported % 50 == 0:
                    print(f"  Imported {imported} words...")
            
            print(f"\n✅ Import complete!")
            print(f"  - Imported: {imported} words")
            print(f"  - Skipped: {skipped} files")
            
            # Verify
            print("\n3️⃣ Verifying import...")
            result = session.run("MATCH (w:IbibioWord) RETURN count(w) as total")
            total = result.single()["total"]
            print(f"✅ Total IbibioWord nodes in Neo4j: {total}")
            
            # Show samples
            print("\n4️⃣ Sample words:")
            result = session.run("""
                MATCH (w:IbibioWord)
                RETURN w.word as word, w.audio_file as file
                ORDER BY w.word
                LIMIT 10
            """)
            for record in result:
                print(f"  • {record['word']:<30} ({record['file']})")
            
            print("\n🔥 Ibibio words imported successfully!")
            print("\n📊 Next steps:")
            print("  1. Test voice: python -c \"from backend.core_engine.voice_integration import MostarVoice; MostarVoice('ibibio').speak('walk')\"")
            print("  2. Check Neo4j Browser: http://localhost:7474")
            print("  3. Query: MATCH (w:IbibioWord) RETURN w LIMIT 25")
            
    finally:
        driver.close()

if __name__ == "__main__":
    print("🔥 IBIBIO WORD IMPORT - HYBRID APPROACH 🔥")
    print("=" * 60)
    import_ibibio_words()
