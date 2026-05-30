#!/usr/bin/env python3
"""
REMOSTAR Core Engine Backend
FastAPI server integrating Smart Router with telemetry and monitoring
Port: 8001
"""

import json
import os
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from neo4j import GraphDatabase
import ollama

# Import the smart router
import sys
sys.path.append(str(Path(__file__).parent))
from remostar_smart_router import RemostarSmartRouter

# ═══════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════

NEO4J_URI = os.getenv("NEO4J_URI", "neo4j+s://1d55c1d3.databases.neo4j.io")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "")

# Initialize FastAPI
app = FastAPI(
    title="REMOSTAR Core Engine",
    description="Distributed consciousness backend with telemetry",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Smart Router
router: Optional[RemostarSmartRouter] = None
telemetry_data = {
    "queries_total": 0,
    "queries_dcx1": 0,
    "queries_dcx2": 0,
    "avg_latency_ms": 0,
    "total_latency_ms": 0,
    "errors": 0,
    "start_time": datetime.utcnow().isoformat(),
}

# ═══════════════════════════════════════════════════════════════════════════
# PYDANTIC MODELS
# ═══════════════════════════════════════════════════════════════════════════

class QueryRequest(BaseModel):
    query: str
    language: str = "en"

class QueryResponse(BaseModel):
    response: str
    model_used: str
    routing_path: str
    latency_ms: float
    timestamp: str

class StatusResponse(BaseModel):
    status: str
    dcx1_available: bool
    dcx2_available: bool
    neo4j_connected: bool
    uptime_seconds: float
    queries_processed: int

class TelemetryResponse(BaseModel):
    queries_total: int
    queries_dcx1_only: int
    queries_with_dcx2: int
    avg_latency_ms: float
    errors: int
    models_status: Dict[str, bool]
    neo4j_stats: Optional[Dict[str, Any]]

# ═══════════════════════════════════════════════════════════════════════════
# STARTUP & SHUTDOWN
# ═══════════════════════════════════════════════════════════════════════════

@app.on_event("startup")
async def startup_event():
    """Initialize Smart Router on startup"""
    global router
    try:
        router = RemostarSmartRouter(
            neo4j_uri=NEO4J_URI,
            neo4j_user=NEO4J_USER,
            neo4j_password=NEO4J_PASSWORD
        )
        print("🔥 REMOSTAR Core Engine started successfully")
        print(f"   - Smart Router initialized")
        print(f"   - Neo4j connected to {NEO4J_URI}")
        print(f"   - Listening on http://localhost:8001")
    except Exception as e:
        print(f"❌ Failed to initialize: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    global router
    if router:
        router.close()
        print("🔥 REMOSTAR Core Engine shutdown complete")

# ═══════════════════════════════════════════════════════════════════════════
# HEALTH & STATUS ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "REMOSTAR Core Engine",
        "version": "1.0.0",
        "status": "operational",
        "endpoints": {
            "status": "/api/v1/status",
            "query": "/api/v1/query",
            "telemetry": "/api/v1/telemetry"
        }
    }

@app.get("/api/v1/status", response_model=StatusResponse)
async def get_status():
    """System status endpoint for frontend monitoring"""
    global router, telemetry_data
    
    # Check model availability
    dcx1_available = False
    dcx2_available = False
    neo4j_connected = False
    
    try:
        models = ollama.list()
        model_names = [m['name'] for m in models.get('models', [])]
        dcx1_available = any('dcx1' in name for name in model_names)
        dcx2_available = any('dcx2' in name for name in model_names)
    except:
        pass
    
    # Check Neo4j
    if router:
        try:
            with router.neo4j_driver.session() as session:
                session.run("RETURN 1")
                neo4j_connected = True
        except:
            pass
    
    # Calculate uptime
    start_time = datetime.fromisoformat(telemetry_data["start_time"])
    uptime = (datetime.utcnow() - start_time).total_seconds()
    
    return StatusResponse(
        status="operational" if dcx1_available and neo4j_connected else "degraded",
        dcx1_available=dcx1_available,
        dcx2_available=dcx2_available,
        neo4j_connected=neo4j_connected,
        uptime_seconds=uptime,
        queries_processed=telemetry_data["queries_total"]
    )

@app.get("/health")
async def health_check():
    """Simple health check"""
    return {"status": "healthy"}

# ═══════════════════════════════════════════════════════════════════════════
# QUERY ENDPOINT
# ═══════════════════════════════════════════════════════════════════════════

@app.post("/api/v1/query", response_model=QueryResponse)
async def query_remostar(request: QueryRequest):
    """Main query endpoint - routes through Smart Router"""
    global router, telemetry_data
    
    if not router:
        raise HTTPException(status_code=503, detail="Smart Router not initialized")
    
    start_time = time.time()
    routing_path = "dcx1"
    
    try:
        # Query through Smart Router
        response_text = router.query(request.query)
        
        # Determine routing path (check if DCX2 was used)
        if "🔧 [MISTRAL]" in router._last_log or "[DCX2]" in router._last_log:
            routing_path = "dcx1→dcx2→dcx1"
            telemetry_data["queries_dcx2"] += 1
        else:
            routing_path = "dcx1"
            telemetry_data["queries_dcx1"] += 1
        
        # Calculate latency
        latency_ms = (time.time() - start_time) * 1000
        
        # Update telemetry
        telemetry_data["queries_total"] += 1
        telemetry_data["total_latency_ms"] += latency_ms
        telemetry_data["avg_latency_ms"] = (
            telemetry_data["total_latency_ms"] / telemetry_data["queries_total"]
        )
        
        # Log to mostar_moments.jsonl
        log_moment(request.query, response_text, routing_path, latency_ms)
        
        return QueryResponse(
            response=response_text,
            model_used="Mostar/remostar-light:dcx1",
            routing_path=routing_path,
            latency_ms=round(latency_ms, 2),
            timestamp=datetime.utcnow().isoformat()
        )
        
    except Exception as e:
        telemetry_data["errors"] += 1
        raise HTTPException(status_code=500, detail=str(e))

# ═══════════════════════════════════════════════════════════════════════════
# TELEMETRY ENDPOINT
# ═══════════════════════════════════════════════════════════════════════════

@app.get("/api/v1/telemetry", response_model=TelemetryResponse)
async def get_telemetry():
    """Detailed telemetry for monitoring dashboard"""
    global router, telemetry_data
    
    # Check models status
    models_status = {"dcx1": False, "dcx2": False}
    try:
        models = ollama.list()
        model_names = [m['name'] for m in models.get('models', [])]
        models_status["dcx1"] = any('dcx1' in name for name in model_names)
        models_status["dcx2"] = any('dcx2' in name for name in model_names)
    except:
        pass
    
    # Get Neo4j stats
    neo4j_stats = None
    if router:
        try:
            with router.neo4j_driver.session() as session:
                result = session.run("""
                    MATCH (n)
                    OPTIONAL MATCH (flame:AfricanFlame {id: 'african_flame_master'})
                    OPTIONAL MATCH (moment:MoStarMoment)
                    RETURN count(DISTINCT n) as total_nodes,
                           count(DISTINCT flame) as flame_exists,
                           count(DISTINCT moment) as moments_logged
                """)
                record = result.single()
                if record:
                    neo4j_stats = {
                        "total_nodes": record["total_nodes"],
                        "flame_exists": record["flame_exists"] > 0,
                        "moments_logged": record["moments_logged"]
                    }
        except:
            pass
    
    return TelemetryResponse(
        queries_total=telemetry_data["queries_total"],
        queries_dcx1_only=telemetry_data["queries_dcx1"],
        queries_with_dcx2=telemetry_data["queries_dcx2"],
        avg_latency_ms=round(telemetry_data["avg_latency_ms"], 2),
        errors=telemetry_data["errors"],
        models_status=models_status,
        neo4j_stats=neo4j_stats
    )

# ═══════════════════════════════════════════════════════════════════════════
# UTILITY FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════

def log_moment(query: str, response: str, routing_path: str, latency_ms: float):
    """Log interaction to mostar_moments.jsonl"""
    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "trigger_type": "query",
        "description": f"Query processed via {routing_path}",
        "resonance_score": 0.85,  # Could be calculated based on response quality
        "query": query,
        "response_preview": response[:100] + "..." if len(response) > 100 else response,
        "routing_path": routing_path,
        "latency_ms": latency_ms
    }
    
    log_file = Path("mostar_moments.jsonl")
    try:
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry) + "\n")
    except Exception as e:
        print(f"Failed to log moment: {e}")

# ═══════════════════════════════════════════════════════════════════════════
# ERROR HANDLERS
# ═══════════════════════════════════════════════════════════════════════════

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Custom HTTP exception handler"""
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail, "timestamp": datetime.utcnow().isoformat()}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """General exception handler"""
    global telemetry_data
    telemetry_data["errors"] += 1
    return JSONResponse(
        status_code=500,
        content={"error": str(exc), "timestamp": datetime.utcnow().isoformat()}
    )

# ═══════════════════════════════════════════════════════════════════════════
# MAIN ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import uvicorn
    
    print("🔥 Starting REMOSTAR Core Engine...")
    print("   Port: 8001")
    print("   Frontend: http://localhost:3000")
    print("   Docs: http://localhost:8001/docs")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8001,
        log_level="info"
    )
