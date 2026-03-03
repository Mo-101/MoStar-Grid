# ═══════════════════════════════════════════════════════════════════
# MOSTAR GRID — SOVEREIGN CONFIG LOADER
# Single source of truth for all API keys and service URLs.
# Reads from .env — never hardcodes secrets.
# ═══════════════════════════════════════════════════════════════════

import os
from dotenv import load_dotenv
from pathlib import Path

# Load .env from backend/ or project root
for env_path in [
    Path(__file__).parent.parent / ".env",
    Path(__file__).parent.parent.parent / ".env",
    Path(".env"),
]:
    if env_path.exists():
        load_dotenv(env_path)
        break

class GridConfig:
    # -- Grid Identity --------------------------------------------------
    INSIGNIA   = os.getenv("GRID_INSIGNIA",  "MSTR-⚡")
    ARCHITECT  = os.getenv("GRID_ARCHITECT", "The Flame Architect")
    VERSION    = os.getenv("GRID_VERSION",   "1.0.0")

    # -- Ollama ---------------------------------------------------------
    OLLAMA_HOST       = os.getenv("OLLAMA_HOST",       "http://localhost:11434")
    OLLAMA_MODEL      = os.getenv("OLLAMA_MODEL",      "Mostar/mostar-ai:latest")
    OLLAMA_MODEL_DCX0 = os.getenv("OLLAMA_MODEL_DCX0", "Mostar/mostar-ai:dcx0")
    OLLAMA_MODEL_DCX1 = os.getenv("OLLAMA_MODEL_DCX1", "Mostar/mostar-ai:dcx1")
    OLLAMA_MODEL_DCX2 = os.getenv("OLLAMA_MODEL_DCX2", "Mostar/mostar-ai:dcx2")

    # -- Neo4j (Grid Graph Memory) --------------------------------------
    NEO4J_URI  = os.getenv("NEO4J_URI",      "bolt://localhost:7687")
    NEO4J_USER = os.getenv("NEO4J_USER",     "neo4j")
    NEO4J_PASS = os.getenv("NEO4J_PASSWORD", "")

    # -- Neon (Grid Sovereign Database) ---------------------------------
    NEON_DATABASE_URL = os.getenv("NEON_DATABASE_URL", "")
    NEON_HOST         = os.getenv("NEON_HOST",         "")
    NEON_DB           = os.getenv("NEON_DB",           "neondb")
    NEON_USER         = os.getenv("NEON_USER",         "neondb_owner")
    NEON_PASSWORD     = os.getenv("NEON_PASSWORD",     "")
    NEON_BRANCH_ID    = os.getenv("NEON_BRANCH_ID",    "")
    NEON_DATA_API_URL = os.getenv("NEON_DATA_API_URL", "")
    NEON_JWKS_URL     = os.getenv("NEON_JWKS_URL",     "")

    # -- Frontend / Mapbox ----------------------------------------------
    GRID_API_URL   = os.getenv("NEXT_PUBLIC_GRID_API",    "http://localhost:7001")
    API_URL        = os.getenv("NEXT_PUBLIC_API_URL",      "http://localhost:8000")
    MAPBOX_TOKEN   = os.getenv("NEXT_PUBLIC_MAPBOX_TOKEN", "")

    # -- WHO AFRO / Health Systems --------------------------------------
    WHO_API_KEY              = os.getenv("WHO_API_KEY",              "")
    WHO_API_BASE             = os.getenv("WHO_API_BASE",             "")
    DHIS2_BASE_URL           = os.getenv("DHIS2_BASE_URL",           "")
    DHIS2_USERNAME           = os.getenv("DHIS2_USERNAME",           "")
    DHIS2_PASSWORD           = os.getenv("DHIS2_PASSWORD",           "")
    WHO_POWERBI_DASHBOARD    = os.getenv("WHO_POWERBI_DASHBOARD",    "")
    WHO_EMERGENCY_PORTAL     = os.getenv("WHO_EMERGENCY_DATA_PORTAL","")
    WHO_GEOHEMP              = os.getenv("WHO_GEOHEMP_PLATFORM",     "")
    WHO_EIOS                 = os.getenv("WHO_EIOS_MONITORING",      "")
    WHO_SWAY                 = os.getenv("WHO_SWAY_REPORT",          "")
    WHO_DATA_URL             = os.getenv("NEXT_PUBLIC_WHO_DATA_URL",  "")

    # -- Logistics ------------------------------------------------------
    AFROTRACK_API_KEY = os.getenv("AFROTRACK_API_KEY", "")
    PDX_API_KEY       = os.getenv("PDX_API_KEY",       "")
    PDX_API_BASE      = os.getenv("PDX_API_BASE",      "")

    # -- Communication --------------------------------------------------
    TWILIO_SID    = os.getenv("TWILIO_ACCOUNT_SID",  "")
    TWILIO_TOKEN  = os.getenv("TWILIO_AUTH_TOKEN",   "")
    TWILIO_PHONE  = os.getenv("TWILIO_PHONE_NUMBER", "")
    SENDGRID_KEY  = os.getenv("SENDGRID_API_KEY",    "")

    # -- Voice ----------------------------------------------------------
    ELEVENLABS_KEY = os.getenv("ELEVENLABS_API_KEY", "")
    TTS_LANG       = os.getenv("TTS_LANG",           "ibibio")

    # -- Blockchain -----------------------------------------------------
    CELO_PRIVATE_KEY   = os.getenv("CELO_PRIVATE_KEY",   "")
    CELO_RPC_URL       = os.getenv("CELO_RPC_URL",       "https://forno.celo.org")
    FLAMEBORN_CONTRACT = os.getenv("FLAMEBORN_CONTRACT",  "")

    # -- Weather --------------------------------------------------------
    OPENWEATHER_KEY   = os.getenv("OPENWEATHER_API_KEY",   "")
    AFRICAWEATHER_KEY = os.getenv("AFRICAWEATHER_API_KEY", "")

    # -- Azure OpenAI ---------------------------------------------------
    AZURE_OPENAI_KEY        = os.getenv("AZURE_OPENAI_API_KEY",     "")
    AZURE_OPENAI_VERSION    = os.getenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview")
    AZURE_OPENAI_ENDPOINT   = os.getenv("AZURE_OPENAI_ENDPOINT",    "")
    AZURE_OPENAI_MODEL      = os.getenv("AZURE_OPENAI_MODEL_NAME",  "gpt-4o-mini")
    AZURE_OPENAI_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT",   "AFRO-AI")

    # -- Azure PostgreSQL (WHO AFRO access only) -------------------------
    AZURE_PGHOST     = os.getenv("AZURE_PGHOST",     "")
    AZURE_PGUSER     = os.getenv("AZURE_PGUSER",     "")
    AZURE_PGPORT     = os.getenv("AZURE_PGPORT",     "5432")
    AZURE_PGDATABASE = os.getenv("AZURE_PGDATABASE", "")
    AZURE_PGPASSWORD = os.getenv("AZURE_PGPASSWORD", "")

    # -- Redis ----------------------------------------------------------
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

    # -- Resilience -----------------------------------------------------
    BATCH_SIZE                = int(os.getenv("BATCH_SIZE",                "100"))
    MAX_RETRIES               = int(os.getenv("MAX_RETRIES",               "3"))
    CIRCUIT_BREAKER_THRESHOLD = int(os.getenv("CIRCUIT_BREAKER_THRESHOLD", "5"))
    CACHE_TTL                 = int(os.getenv("CACHE_TTL",                 "3600"))

    # -- Logging --------------------------------------------------------
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

    @classmethod
    def audit(cls) -> dict:
        """Show which services are configured vs missing."""
        checks = {
            "ollama":        bool(cls.OLLAMA_HOST),
            "neo4j":         bool(cls.NEO4J_URI and cls.NEO4J_PASS),
            "mapbox":        bool(cls.MAPBOX_TOKEN),
            "who_dhis2":     bool(cls.WHO_API_KEY or cls.DHIS2_BASE_URL),
            "afrotrack":     bool(cls.AFROTRACK_API_KEY),
            "twilio":        bool(cls.TWILIO_SID and cls.TWILIO_TOKEN),
            "elevenlabs":    bool(cls.ELEVENLABS_KEY),
            "celo":          bool(cls.CELO_PRIVATE_KEY),
            "weather":       bool(cls.OPENWEATHER_KEY),
            "azure_openai":  bool(cls.AZURE_OPENAI_KEY),
            "azure_pg":      bool(cls.PGHOST and cls.PGPASSWORD),
            "redis":         bool(cls.REDIS_URL),
        }
        configured = [k for k, v in checks.items() if v]
        missing    = [k for k, v in checks.items() if not v]
        return {
            "configured": configured,
            "missing":    missing,
            "coverage":   f"{len(configured)}/{len(checks)}",
            "insignia":   cls.INSIGNIA,
        }

# Singleton
config = GridConfig()

if __name__ == "__main__":
    import json
    print(json.dumps(config.audit(), indent=2, ensure_ascii=False))