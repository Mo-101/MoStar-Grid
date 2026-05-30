import sys
import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any

# Add the project root to sys.path to allow imports from backend
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

from backend.memory_layer.retriever import MoStarMemory

app = FastAPI(title="MoStar Memory API")

# Initialize memory store
try:
    memory_store = MoStarMemory()
    print("Memory store loaded successfully.")
except Exception as e:
    print(f"Failed to load memory store: {e}")
    memory_store = None

class MemoryQuery(BaseModel):
    query: str
    k: int = 5

class MemoryResponse(BaseModel):
    query: str
    results: List[Dict[str, Any]]

@app.get("/")
def health_check():
    return {"status": "online", "service": "MoStar Memory API"}

@app.post("/memory_query", response_model=MemoryResponse)
def query_memory(q: MemoryQuery):
    if not memory_store:
        raise HTTPException(status_code=503, detail="Memory store not initialized")
    
    try:
        # The retriever returns a list of Documents
        # We need to serialize them for the API response
        docs = memory_store.search(q.query, k=q.k)
        
        results = []
        for doc in docs:
            results.append({
                "content": doc.page_content,
                "metadata": doc.metadata
            })
            
        return {"query": q.query, "results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
