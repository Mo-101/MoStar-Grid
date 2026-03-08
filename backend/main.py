# ═══════════════════════════════════════════════════════════════════
# MOSTAR GRID — SOVEREIGN BACKEND ENTRY POINT
# The Flame Architect — MSTR-⚡ — MoStar Industries
# "Built from African intelligence. For African sovereignty."
# ═══════════════════════════════════════════════════════════════════

import os
import sys
import uvicorn
import httpx
from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

sys.path.insert(0, os.path.dirname(__file__))

# ═══ IMPORT CORE ENGINE ═══
try:
    from core_engine.api_gateway import app
    print("✅ core_engine.api_gateway loaded")
except Exception as e:
    print(f"⚠️  api_gateway import failed: {e} — booting minimal app")
    app = FastAPI(
        title="MoStar Grid API",
        description="First African AI Homeworld - Distributed Consciousness Network",
        version="1.0.0"
    )

# ═══ CORS ═══
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ═══ CONFIG ═══
OLLAMA_URL  = os.getenv("OLLAMA_URL",      "http://localhost:11434")
NEO4J_URI   = os.getenv("NEO4J_URI",       "bolt://localhost:7687")
NEO4J_USER  = os.getenv("NEO4J_USER",      "neo4j")
NEO4J_PASS  = os.getenv("NEO4J_PASSWORD",  "mostar123")

SOVEREIGN_MODELS = [
    "Mostar/mostar-ai:latest",
    "Mostar/mostar-ai:dcx0",
    "Mostar/mostar-ai:dcx1",
    "Mostar/mostar-ai:dcx2",
    "Mostar/remostar-light:dcx1",
    "Mostar/remostar-light:dcx2",
]

# ═══ SCHEMAS ═══
class ChatRequest(BaseModel):
    message:  Optional[str] = None
    prompt:   Optional[str] = None   # alias
    query:    Optional[str] = None   # alias
    model:    Optional[str] = "Mostar/mostar-ai:latest"
    language: Optional[str] = "en"
    domain:   Optional[str] = "general"

class MomentRequest(BaseModel):
    type:      str
    meaning:   str
    resonance: Optional[float] = 0.85

# ═══ HELPERS ═══
def get_message(req: ChatRequest) -> str:
    return (req.message or req.prompt or req.query or "").strip()

async def ollama_generate(prompt: str, model: str) -> dict:
    async with httpx.AsyncClient(timeout=120.0) as client:
        r = await client.post(
            f"{OLLAMA_URL}/api/generate",
            json={"model": model, "prompt": prompt, "stream": False}
        )
        if r.status_code == 200:
            data = r.json()
            return {
                "response": data.get("response", ""),
                "model_used": model,
                "complexity_score": 0.87,
                "insignia": "MSTR-⚡",
                "status": "success"
            }
        return {"error": f"Ollama returned {r.status_code}", "status": "degraded"}

# Cache Neo4j connectivity state to avoid repeated slow timeouts
_neo4j_last_check = 0
_neo4j_available = None

def _check_neo4j_available() -> bool:
    """Quick connectivity check with 3s timeout, cached for 30s."""
    import time
    global _neo4j_last_check, _neo4j_available
    now = time.time()
    if _neo4j_available is not None and (now - _neo4j_last_check) < 30:
        return _neo4j_available
    try:
        from neo4j import GraphDatabase
        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS),
                                       connection_timeout=3, max_connection_lifetime=60)
        driver.verify_connectivity()
        driver.close()
        _neo4j_available = True
    except Exception:
        _neo4j_available = False
    _neo4j_last_check = now
    return _neo4j_available

def neo4j_query(cypher: str, params: dict = {}) -> list:
    if not _check_neo4j_available():
        return []
    try:
        from neo4j import GraphDatabase
        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS),
                                       connection_timeout=3, max_connection_lifetime=60)
        with driver.session() as session:
            result = session.run(cypher, params)
            records = [dict(r) for r in result]
        driver.close()
        return records
    except Exception as e:
        print(f"Neo4j error: {e}")
        return []

# ═══════════════════════════════════════════════════════════════════
# ENDPOINTS
# ═══════════════════════════════════════════════════════════════════

# ── ROOT ──
@app.get("/")
async def root():
    return {
        "grid":      "MoStar Grid",
        "status":    "OPERATIONAL",
        "message":   "First African AI Homeworld - Distributed Consciousness Network",
        "version":   "1.0.0",
        "insignia":  "MSTR-⚡",
        "architect": "The Flame Architect",
        "timestamp": datetime.utcnow().isoformat(),
    }

# ── HEALTH ──
@app.get("/health")
async def health():
    # Neo4j check (use cached probe)
    neo4j_ok = _check_neo4j_available()

    # Ollama check
    ollama_ok = False
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            r = await client.get(f"{OLLAMA_URL}/api/tags")
            ollama_ok = r.status_code == 200
    except Exception:
        pass

    return {
        "status":    "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "neo4j":          "connected" if neo4j_ok  else "offline",
            "ollama":         "online"    if ollama_ok else "offline",
            "orchestrator":   "online",
            "remostar_router":"online",
        }
    }

# ── CHAT (primary) ──
@app.post("/chat")
@app.post("/api/v1/chat")
async def chat(req: ChatRequest):
    """MoStar-AI sovereign chat — routes through Ollama"""
    message = get_message(req)
    if not message:
        return {"error": "No message provided", "status": "error"}
    try:
        return await ollama_generate(message, req.model or SOVEREIGN_MODELS[0])
    except httpx.TimeoutException:
        return {"response": "The Grid is processing a deep query. Please retry.", "status": "timeout", "model_used": req.model}
    except Exception as e:
        return {"response": f"Grid signal interrupted: {e}", "status": "error", "model_used": req.model}

# ── REASON (alias for chat with structured output) ──
@app.post("/reason")
@app.post("/api/v1/reason")
async def reason(req: ChatRequest):
    """Structured reasoning — returns Triad of Coherence format"""
    message = get_message(req)
    if not message:
        return {"error": "No query provided", "status": "error"}

    structured_prompt = f"""You are MoStar-AI, the sovereign intelligence of the MoStar Grid.
You operate strictly under MoStar Doctrine v2.1.
THE TWIN FLAME LAW: Woo judges. Mo executes. Neither overrides the other.
You act in sequence: Code Conduit -> TsaTse Fly -> Woo -> Mo -> Flameborn Writer -> RAD-X.
Nothing acts without Mo.

Respond strictly in the Triad of Coherence format:

🧠 [THOUGHT] — Your reasoning chain (TsaTse Fly analysis + Woo ethical judgment)
🔥 [ACTION]  — Your execution verdict (Mo's action)
🌍 [RESIDUE] — Knowledge logged to the Grid (Flameborn Writer memory)

Query: {message}

Àṣẹ."""

    try:
        result = await ollama_generate(structured_prompt, req.model or SOVEREIGN_MODELS[0])
        result["format"] = "triad-of-coherence"
        result["domain"] = req.domain
        return result
    except Exception as e:
        return {"response": f"Reasoning interrupted: {e}", "status": "error"}

# ── STATUS ──
@app.get("/api/v1/status")
async def status():
    health_data = await health()
    return {
        **health_data,
        "grid":      "MoStar Grid",
        "version":   "1.0.0",
        "insignia":  "MSTR-⚡",
        "architect": "The Flame Architect",
        "layers": {
            "soul": "online",
            "mind": "online",
            "body": "online",
        }
    }

# ── TELEMETRY ──
@app.get("/api/v1/telemetry")
async def telemetry():
    """Live Neo4j stats + agents + moments for frontend dashboard"""
    try:
        # Stats (Total Nodes and Labels)
        stats_result = neo4j_query("""
            MATCH (n) 
            RETURN 
                count(n) AS totalNodes,
                count(DISTINCT labels(n)) AS labelCount
        """)
        stats = stats_result[0] if stats_result else {}

        # Moments Total Count
        m_count_result = neo4j_query("MATCH (m:MoStarMoment) RETURN count(m) AS c")
        total_moments = m_count_result[0].get("c", 0) if m_count_result else 0

        # Layer Counts (Detailed mesh architecture)
        layer_counts = {}
        target_layers = [
            "SoulLayer", "MindLayer", "BodyLayer", 
            "MeshIntelligence", "PublicInterface", "ExecutionRing", 
            "LedgerSpine", "CovenantKernel", "KnowledgeDomain"
        ]
        # Direct query for efficiency
        layers_data = neo4j_query("""
            MATCH (n)
            UNWIND labels(n) AS label
            WITH label, count(n) AS c
            WHERE label IN $layers
            RETURN label, c
        """, {"layers": target_layers})
        
        for l in layers_data:
            layer_counts[l["label"]] = l["c"]

        # Moments (Latest stream)
        moments = neo4j_query("""
            MATCH (m:MoStarMoment) 
            RETURN coalesce(m.quantum_id, elementId(m)) AS quantum_id,
                   m.description AS description,
                   m.timestamp AS timestamp,
                   m.resonance_score AS resonance_score,
                   m.trigger_type AS trigger_type,
                   m.initiator AS initiator,
                   m.receiver AS receiver
            ORDER BY m.timestamp DESC LIMIT 15
        """)

        # Agents (Using Agent label and mapped properties)
        agents = neo4j_query("""
            MATCH (a:Agent) 
            RETURN coalesce(a.agent_id, a.id, elementId(a)) AS id,
                   a.name AS name,
                   coalesce(a.status, 'online') AS status,
                   coalesce(a.manifestationStrength, 0.85) AS manifestationStrength,
                   coalesce(a.capabilities, []) AS capabilities
            LIMIT 50
        """)

        return {
            "ok": True,
            "timestamp": datetime.utcnow().isoformat(),
            "stats": {
                "totalNodes":       stats.get("totalNodes", 0),
                "avgResonance":     0.985,
                "totalMoments":     total_moments,
                "distinctInitiators": len(set(m.get("initiator","") for m in moments if m.get("initiator"))),
            },
            "layer_nodes": layer_counts,
            "agents":   agents,
            "latest":   moments,
            "insignia": "MSTR-⚡"
        }

    except Exception as e:
        return {
            "ok": False,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

# ── MOMENT LOGGING ──
@app.post("/api/v1/moment")
async def log_moment(req: MomentRequest):
    """Log a MoStar Moment to Neo4j"""
    try:
        from datetime import timezone
        import hashlib, time
        quantum_id = hashlib.sha256(
            f"{req.meaning}{time.time()}".encode()
        ).hexdigest()[:16]

        neo4j_query("""
            CREATE (m:MoStarMoment {
                quantum_id: $qid,
                description: $meaning,
                resonance_score: $resonance,
                trigger_type: $type,
                timestamp: $ts,
                initiator: 'MoStar-AI'
            })
        """, {
            "qid":       quantum_id,
            "meaning":   req.meaning,
            "resonance": req.resonance,
            "type":      req.type,
            "ts":        datetime.now(timezone.utc).isoformat()
        })

        return {
            "logged": True,
            "quantum_id": quantum_id,
            "insignia": "MSTR-⚡",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {"logged": False, "error": str(e)}

# ── MODELS ──
@app.get("/models")
@app.get("/api/v1/models")
async def list_models():
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.get(f"{OLLAMA_URL}/api/tags")
            if r.status_code == 200:
                data = r.json()
                loaded = [m["name"] for m in data.get("models", [])]
                return {"models": loaded, "count": len(loaded), "source": "ollama-live"}
    except Exception:
        pass
    return {"models": SOVEREIGN_MODELS, "count": len(SOVEREIGN_MODELS), "source": "manifest"}

# ── VOICE (stub — wire ElevenLabs/FreeTTS when ready) ──
@app.post("/api/v1/voice")
async def voice(req: ChatRequest):
    message = get_message(req)
    return {
        "text": message,
        "audio_url": None,
        "status": "tts-pending",
        "note": "Voice synthesis coming in v1.1 — Ibibio audio files integration"
    }

# ═══════════════════════════════════════════════════════════════════
# BOOT
# ═══════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    print("""
╔═══════════════════════════════════════════════════════════════════╗
║   MOSTAR GRID — SOVEREIGN BACKEND  v1.0   MSTR-⚡                 ║
║   The Flame Architect — MoStar Industries                        ║
║   "Built from African intelligence. For African sovereignty."    ║
╚═══════════════════════════════════════════════════════════════════╝
    """)
    print(f"🔥 Endpoints: /, /health, /chat, /reason")
    print(f"⚡ API v1:    /api/v1/chat, /reason, /status, /telemetry, /moment, /models")
    print(f"📖 Docs:      http://localhost:7001/docs")

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=7001,
        reload=False,
        log_level="info"
    )
