from fastapi import FastAPI
from api.routes import router

app = FastAPI(
    title="MoStar Core Kernel API",
    description="The API gateway for the FGrid knowledge fabric and MoStar Executive Intelligence.",
    version="0.1.0"
)

app.include_router(router, prefix="/api")

@app.get("/", summary="Root endpoint confirming kernel health")
def read_root():
    return {
        "status": "Online",
        "kernel": "MoStar AI Core",
        "world_model": "FGrid"
    }
