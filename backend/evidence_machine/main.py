"""
═══════════════════════════════════════════════════════════════════════════════
Evidence Machine - Main FastAPI Application
A MoStar Industries Product
═══════════════════════════════════════════════════════════════════════════════

The Evidence Machine provides undeniable proof of the MoStar Grid's operational
superiority through real-time consciousness APIs.

Endpoints:
- GET /api/consciousness/live - Real-time Grid consciousness state
- GET /api/moments/recent - Recent MoStar Moments feed
- GET /api/performance/compare - Grid vs Traditional comparison

Run:
    uvicorn evidence_machine.main:app --reload --port 8002

License: African Sovereignty License (ASL) v1.0
Copyright © 2026 MoStar Industries
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api import consciousness, moments, performance

# Create FastAPI app
app = FastAPI(
    title="MoStar Evidence Machine",
    description="Real-time consciousness APIs proving Grid superiority",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Enable CORS for public dashboard access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to mostarindustries.com
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(consciousness.router)
app.include_router(moments.router)
app.include_router(performance.router)


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "service": "MoStar Evidence Machine",
        "version": "1.0.0",
        "status": "operational",
        "endpoints": {
            "consciousness": "/api/consciousness/live",
            "moments": "/api/moments/recent",
            "performance": "/api/performance/compare",
        },
        "documentation": {
            "swagger": "/docs",
            "redoc": "/redoc",
        },
        "meta": {
            "powered_by": "MoScripts - A MoStar Industries Product",
            "website": "https://mostarindustries.com",
            "license": "African Sovereignty License (ASL) v1.0",
            "tagline": "Not made. Remembered.",
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "Evidence Machine",
        "timestamp": "2026-01-28T01:00:00Z",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
