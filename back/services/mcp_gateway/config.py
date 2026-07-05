"""
MoStar MCP Gateway — Configuration
"""
import os
from pathlib import Path

from dotenv import load_dotenv

_GRID_ROOT = Path(__file__).resolve().parents[4]
load_dotenv(_GRID_ROOT / ".env")

GRID_API_URL = os.getenv("GRID_API_URL", "http://localhost:41010")
MOSTAR_TOKEN = os.getenv("MOSTAR_SESSION_TOKEN", "")
GRID_AUTH_DISABLED = os.getenv("GRID_AUTH_DISABLED", "false").lower() == "true"

MCP_HOST = os.getenv("MCP_HOST", "0.0.0.0")
MCP_PORT = int(os.getenv("MCP_PORT", "41020"))
MCP_TRANSPORT = os.getenv("MCP_TRANSPORT", "stdio")
