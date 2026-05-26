"""
MoStar Grid — Configuration
The Flame Architect · MoStar Industries
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# === Paths ===
GRID_ROOT = Path(__file__).parent.parent
DATA_DIR = GRID_ROOT / "data"
LOGS_DIR = GRID_ROOT / "logs"

# === Neo4j ===
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "mostar2026")
NEO4J_DATABASE = os.getenv("NEO4J_DATABASE", "neo4j")

# === Ollama ===
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
DCX0_MODEL = os.getenv("DCX0_MODEL", "phi4:latest")          # Mind
DCX1_MODEL = os.getenv("DCX1_MODEL", "qwen2.5:1.5b")        # Soul
DCX2_MODEL = os.getenv("DCX2_MODEL", "mistral:latest")       # Body

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
