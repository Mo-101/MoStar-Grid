"""
MoStar Grid — Configuration
The Flame Architect · MoStar Industries
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# === Paths ===
GRID_ROOT = Path(__file__).parent.parent
DATA_DIR = GRID_ROOT / "data"
LOGS_DIR = GRID_ROOT / "logs"

load_dotenv(GRID_ROOT / ".env")


def _required_env(name: str) -> str:
    value = os.getenv(name)
    if value is None:
        raise RuntimeError(f"{name} is required. Set it in {GRID_ROOT / '.env'}")
    return value


def _env(name: str, default: str) -> str:
    return os.getenv(name, default)


# === Cluster Identity ===
MOSTAR_CLUSTER_ID = _env("MOSTAR_CLUSTER_ID", "nairobi-alpha")
MOSTAR_CLUSTER_NAME = _env("MOSTAR_CLUSTER_NAME", "Nairobi Health Cluster")
MOSTAR_CLUSTER_REGION = _env("MOSTAR_CLUSTER_REGION", "east-africa")

CLUSTER_DIR = DATA_DIR / "clusters" / MOSTAR_CLUSTER_ID
APPROVAL_QUEUE_PATH = CLUSTER_DIR / "approval_queue" / "proposals.jsonl"
PROVENANCE_PATH = CLUSTER_DIR / "provenance" / "events.jsonl"
MCP_CLUSTER_API_URL = _env("MCP_CLUSTER_API_URL", "http://localhost:41010")
PEER_KEYS_PATH = CLUSTER_DIR / "peers" / "cluster_keys.json"
EVIDENCE_DIR = CLUSTER_DIR / "evidence"


def cluster_metadata() -> dict:
    return {
        "cluster_id": MOSTAR_CLUSTER_ID,
        "cluster_name": MOSTAR_CLUSTER_NAME,
        "cluster_region": MOSTAR_CLUSTER_REGION,
    }


def ensure_cluster_dirs() -> None:
    APPROVAL_QUEUE_PATH.parent.mkdir(parents=True, exist_ok=True)
    PROVENANCE_PATH.parent.mkdir(parents=True, exist_ok=True)
    PEER_KEYS_PATH.parent.mkdir(parents=True, exist_ok=True)
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)

# === Neo4j ===
NEO4J_URI = _required_env("NEO4J_URI")
NEO4J_USER = _required_env("NEO4J_USER")
NEO4J_PASSWORD = _required_env("NEO4J_PASSWORD")
NEO4J_DATABASE = _required_env("NEO4J_DATABASE")

# === Ollama ===
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
DCX0_MODEL = os.getenv("DCX0_MODEL", "Mostar/mostar-ai:dcx0")  # Mind
DCX1_MODEL = os.getenv("DCX1_MODEL", "Mostar/mostar-ai:dcx1")  # Soul
DCX2_MODEL = os.getenv("DCX2_MODEL", "Mostar/mostar-ai:dcx2")  # Body

# === Truth Gate Elemental Thresholds ===
TRUTH_THRESHOLDS = {
    "ikang":  float(os.getenv("TRUTH_IKANG", "0.75")),   # Fire 🜂
    "mmong":  float(os.getenv("TRUTH_MMONG", "0.70")),    # Water 🜄
    "afim":   float(os.getenv("TRUTH_AFIM", "0.65")),     # Air 🜁
    "isong":  float(os.getenv("TRUTH_ISONG", "0.80")),    # Earth 🜃
}

# === Woo Judgment ===
WOO_THRESHOLD = float(os.getenv("WOO_THRESHOLD", "0.97"))

# === Grid API ===
GRID_HOST = os.getenv("GRID_HOST", "0.0.0.0")
GRID_PORT = int(os.getenv("GRID_PORT", "41010"))

# === Sovereign Port Registry (41xxx band) ===
PORTS = {
    "grid_api": 41010,
    "grid_ws": 41011,
    "grid_ui": 41012,
}

# === MoStar Moment Seal ===
SEAL_GLYPH = "🜃∴🜂"
SEAL_SIGNATURE = "The Flame Architect"
