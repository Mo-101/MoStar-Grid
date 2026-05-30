"""
IBIBIO TTS SYSTEM - Flask API (MOSTAR EDITION)
Serves Ibibio words with audio from Neo4j
Credentials: neo4j / mostar123
"""

from flask import Flask, jsonify, send_from_directory, request
from flask_cors import CORS
from neo4j import GraphDatabase
import os
from pathlib import Path

app = Flask(__name__)
CORS(app)

# Neo4j Connection - MOSTAR CREDENTIALS
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "mostar123"  # ✅ CORRECT PASSWORD

# Audio files location
AUDIO_DIR = Path("C:/Users/AI/Documents/MoStar/Mo Docs/neo4j-community-2025.10.1/import/Ibibio_audio")

# Test connection on startup
try:
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    with driver.session() as session:
        result = session.run("RETURN 1 AS test")
        result.single()
    print("✅ Neo4j connection successful!")
    print("🔥 Connected to MOSTAR Universe!")
except Exception as e:
    print("❌ Neo4j connection FAILED!")
    print(f"Error: {e}")
    driver = None

def get_db():
    if driver is None:
        raise Exception("Neo4j connection not available")
    return driver.session()

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    neo4j_status = "connected" if driver else "disconnected"
    
    return jsonify({
        "status": "online", 
        "message": "Iko Ikang - Voice of Flame is Active",
        "audio_dir_exists": AUDIO_DIR.exists(),
        "neo4j_status": neo4j_status,
        "universe": "MOSTAR"
    }), 200

# =========================================================
# 🎵 AUDIO ENDPOINTS
# =========================================================

@app.route('/api/audio/semantic/<term>', methods=['GET'])
def get_semantic_audio(term):
    """
    Finds audio by English meaning (e.g., 'mother', 'strength').
    Looks up the AudioSample node where term matches.
    """
    session = get_db()
    try:
        # Search DB for the filename associated with the semantic term
        result = session.run("""
            MATCH (a:AudioSample)
            WHERE toLower(a.term) = toLower($term)
            RETURN a.filename AS filename
            LIMIT 1
        """, term=term)
        
        record = result.single()
        
        if not record:
            return jsonify({"error": f"No audio found for term: {term}"}), 404
            
        filename = record['filename']
        
        # Check if file exists
        file_path = AUDIO_DIR / filename
        if not file_path.exists():
            return jsonify({"error": f"Audio file exists in DB but not on filesystem: {filename}"}), 404
        
        # Use send_from_directory for secure serving
        return send_from_directory(AUDIO_DIR, filename, mimetype='audio/mpeg')
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()

@app.route('/api/audio/<filename>', methods=['GET'])
def serve_audio_file(filename):
    """Serve a specific audio file by filename (Secure)"""
    try:
        file_path = AUDIO_DIR / filename
        if not file_path.exists():
            return jsonify({
                "error": f"File not found: {filename}",
                "audio_dir": str(AUDIO_DIR),
                "file_exists": file_path.exists()
            }), 404
        return send_from_directory(AUDIO_DIR, filename, mimetype='audio/mpeg')
    except Exception as e:
        return jsonify({"error": str(e)}), 404

# =========================================================
# 📖 WORD DATA ENDPOINTS
# =========================================================

@app.route('/api/words', methods=['GET'])
def get_all_words():
    """Get all Ibibio words with their linked audio"""
    session = get_db()
    try:
        result = session.run("""
            MATCH (w:IbibioWord)
            OPTIONAL MATCH (a:AudioSample)-[:VOICES]->(w)
            RETURN w.word AS word, 
                   w.english AS english, 
                   w.speaker AS speaker,
                   a.filename AS audio_file
            ORDER BY w.english
            LIMIT 200
        """)
        
        words = [dict(record) for record in result]
        return jsonify({"count": len(words), "words": words}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()

@app.route('/api/words/search', methods=['GET'])
def search_words():
    """Search words and return linked audio"""
    query = request.args.get('q', '').lower()
    
    if not query:
        return jsonify({"error": "Query parameter 'q' required"}), 400
    
    session = get_db()
    try:
        result = session.run("""
            MATCH (w:IbibioWord)
            WHERE toLower(w.english) CONTAINS $query OR toLower(w.word) CONTAINS $query
            OPTIONAL MATCH (a:AudioSample)-[:VOICES]->(w)
            RETURN w.word AS word, 
                   w.english AS english, 
                   w.speaker AS speaker,
                   a.filename AS audio_file
            LIMIT 50
        """, query=query)
        
        words = [dict(record) for record in result]
        return jsonify({"count": len(words), "words": words}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get database statistics"""
    session = get_db()
    try:
        result = session.run("""
            MATCH (w:IbibioWord)
            WITH count(w) AS total_words
            OPTIONAL MATCH (a:AudioSample)
            WITH total_words, count(a) AS total_audio
            OPTIONAL MATCH (e:Entity)
            WITH total_words, total_audio, count(e) AS total_entities
            OPTIONAL MATCH (o:OduIfa)
            RETURN total_words, 
                   total_audio, 
                   total_entities,
                   count(o) AS total_odu
        """)
        
        stats = dict(result.single())
        return jsonify(stats), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()

@app.route('/api/debug/audio-samples', methods=['GET'])
def debug_audio_samples():
    """Debug endpoint to check AudioSample nodes"""
    session = get_db()
    try:
        result = session.run("""
            MATCH (a:AudioSample)
            RETURN count(a) AS total,
                   collect(a.term)[0..10] AS sample_terms
        """)
        
        data = dict(result.single())
        return jsonify(data), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()

if __name__ == '__main__':
    print("=" * 60)
    print("🔥 IKO IKANG - VOICE OF FLAME")
    print("   MOSTAR UNIVERSE API")
    print("=" * 60)
    print(f"📊 Neo4j: {NEO4J_URI}")
    print(f"👤 User: {NEO4J_USER}")
    print(f"🎵 Audio: {AUDIO_DIR}")
    print(f"🌐 Server: http://localhost:5000")
    print("=" * 60)
    
    if driver is None:
        print("\n⚠️  WARNING: Neo4j connection failed!")
        print("   API endpoints will not work.")
    
    app.run(debug=True, host='0.0.0.0', port=5000)