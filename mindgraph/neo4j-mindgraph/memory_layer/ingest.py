import json
import os
import shutil
import argparse
import time
from typing import List, Dict, Any
from pathlib import Path
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document

# Configuration
BASE_DIR = Path(__file__).parent.parent.parent
JSON_SOURCE = BASE_DIR / 'exports' / 'activation_subgraph.json'
STORE_PATH = BASE_DIR / 'backend' / 'data' / 'memory_store'
BACKUP_PATH = BASE_DIR / 'backend' / 'data' / 'memory_store_backup'
MODEL_NAME = "all-MiniLM-L6-v2"

def load_moments(json_path: Path) -> List[Dict[str, Any]]:
    """Load MoStarMoments from the JSON export."""
    if not json_path.exists():
        raise FileNotFoundError(f"Source file not found: {json_path}")
        
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    moments = [
        node for node in data.get("nodes", []) 
        if node.get("type") == "MoStarMoment"
    ]
    return moments

def create_documents(moments: List[Dict[str, Any]]) -> List[Document]:
    """Convert moments to LangChain Documents."""
    docs = []
    for m in moments:
        data = m.get("data", {})
        
        # Construct a rich semantic representation
        content = (
            f"Moment: {data.get('description', 'Unknown Event')}\n"
            f"Era: {data.get('era', 'Unknown')}\n"
            f"Resonance: {data.get('resonance', 0.0)}\n"
            f"Initiator: {data.get('initiator', 'Unknown')}\n"
            f"Receiver: {data.get('receiver', 'Unknown')}\n"
            f"Timestamp: {data.get('timestamp', 'Unknown')}"
        )
        
        # Metadata for filtering and context
        metadata = {
            "id": m.get("id"),
            "timestamp": data.get("timestamp"),
            "era": data.get("era"),
            "resonance": data.get("resonance"),
            "type": "MoStarMoment",
            "ingested_at": time.time()
        }
        
        docs.append(Document(page_content=content, metadata=metadata))
    return docs

def ingest_memory(refresh: bool = False, source: str = None):
    """Main ingestion process."""
    source_path = Path(source) if source else JSON_SOURCE
    
    print(f"📂 Loading moments from {source_path}...")
    try:
        moments = load_moments(source_path)
    except FileNotFoundError:
        print(f"❌ Source file not found: {source_path}")
        return

    print(f"   Found {len(moments)} moments.")
    
    print("📄 Converting to documents...")
    docs = create_documents(moments)
    if not docs:
        print("⚠️ No documents to ingest.")
        return
    
    print(f"🧠 Initializing embeddings ({MODEL_NAME})...")
    embeddings = HuggingFaceEmbeddings(model_name=MODEL_NAME)
    
    if refresh:
        print("🔄 Refresh mode: Rebuilding index from scratch...")
        if STORE_PATH.exists():
            print(f"   Backing up existing store to {BACKUP_PATH}...")
            if BACKUP_PATH.exists():
                shutil.rmtree(BACKUP_PATH)
            shutil.copytree(STORE_PATH, BACKUP_PATH)
            shutil.rmtree(STORE_PATH)
            
        print("🏗️  Building new FAISS index...")
        vectorstore = FAISS.from_documents(docs, embeddings)
        
    else:
        print("➕ Append mode: Adding to existing index...")
        if STORE_PATH.exists() and (STORE_PATH / "index.faiss").exists():
             try:
                vectorstore = FAISS.load_local(str(STORE_PATH), embeddings, allow_dangerous_deserialization=True)
                vectorstore.add_documents(docs)
             except Exception as e:
                 print(f"❌ Failed to load existing index: {e}. Falling back to create new.")
                 vectorstore = FAISS.from_documents(docs, embeddings)
        else:
            print("   No existing index found. Creating new...")
            vectorstore = FAISS.from_documents(docs, embeddings)
    
    print(f"💾 Saving to {STORE_PATH} (Atomic Swap)...")
    STORE_PATH.mkdir(parents=True, exist_ok=True)
    
    # Save to a temporary location first for atomic-like swap logic
    temp_path = STORE_PATH.parent / "temp_memory_store"
    if temp_path.exists():
        shutil.rmtree(temp_path)
    temp_path.mkdir(parents=True, exist_ok=True)
    
    vectorstore.save_local(str(temp_path))
    
    # Swap
    backup_path = STORE_PATH.parent / f"backup_memory_store_{int(time.time())}"
    if STORE_PATH.exists():
        STORE_PATH.rename(backup_path)
    temp_path.rename(STORE_PATH)
    
    print("✅ Memory ingestion complete.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="MoStar Memory Ingestion")
    parser.add_argument("--refresh", action="store_true", help="Full index rebuild with backup")
    parser.add_argument("--append", action="store_true", help="Append to index")
    parser.add_argument("--source", type=str, help="Path to source JSON file")
    
    args = parser.parse_args()
    
    # Refresh logic already handles rebuild, append is the alternative
    ingest_memory(refresh=args.refresh, source=args.source)
