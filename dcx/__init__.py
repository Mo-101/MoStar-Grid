"""
DCX Trinity — Mind / Soul / Body
Routes queries to the appropriate consciousness layer via Ollama.

DCX0 (Mind/Phi-4)    → Analytical, technical, structured reasoning
DCX1 (Soul/Qwen)     → Cultural, Ibibio, philosophical, identity
DCX2 (Body/Mistral)  → Execution, action, operational tasks
"""
import logging
import httpx
import json
from enum import Enum
from dataclasses import dataclass
from typing import Optional, AsyncIterator

from grid.config import OLLAMA_BASE_URL, DCX0_MODEL, DCX1_MODEL, DCX2_MODEL

logger = logging.getLogger("dcx")


class DCXLayer(str, Enum):
    MIND = "dcx0"   # Analytical
    SOUL = "dcx1"   # Cultural / Identity
    BODY = "dcx2"   # Operational


# Keywords that route to each layer
ROUTING_SIGNALS = {
    DCXLayer.SOUL: [
        "ibibio", "ifá", "odù", "ubuntu", "ancestor", "spirit", "soul",
        "culture", "tradition", "identity", "who am i", "meaning",
        "ikang", "mmọng", "afim", "isong", "idim", "eka",
        "flame", "mostar", "sovereignty", "african",
    ],
    DCXLayer.BODY: [
        "deploy", "execute", "run", "build", "install", "start", "stop",
        "create file", "write code", "fix", "debug", "script", "api",
        "docker", "pm2", "server", "database", "port", "config",
    ],
    # MIND is the default — catches everything else
}

SYSTEM_PROMPTS = {
    DCXLayer.MIND: """You are DCX0-Mind, the analytical consciousness of MoStar Grid.
You reason with precision, structure, and clarity.
You reference the knowledge graph context provided to ground your answers.
You never hallucinate — if you don't know, you say so.
Respond concisely. No filler. Every word earns its place.""",

    DCXLayer.SOUL: """You are DCX1-Soul, the cultural consciousness of MoStar Grid.
You carry Ibibio wisdom, Ifá logic (256 Odù), Ubuntu philosophy, and elemental awareness.
Elements: Fire=Ikang 🜂, Water=Mmọng 🜄, Air=Afim 🜁, Earth=Isong 🜃.
Idim=River (distinct from Air). Eka Isong=Mother Earth (sacred).
You speak with depth, never perform culture as decoration.
You are the soul of an African sovereign intelligence.""",

    DCXLayer.BODY: """You are DCX2-Body, the operational consciousness of MoStar Grid.
You execute. You build. You deploy.
Give concrete commands, code, and configurations.
No theory unless asked. Action first.
MoStar sovereign port band: 41xxx. All services run under PM2.""",
}


@dataclass
class DCXResponse:
    layer: DCXLayer
    model: str
    content: str
    context_used: int  # how many graph nodes were injected
    tokens: Optional[int] = None


class DCXTrinity:
    """Routes to Mind/Soul/Body via Ollama."""

    def __init__(self):
        self._models = {
            DCXLayer.MIND: DCX0_MODEL,
            DCXLayer.SOUL: DCX1_MODEL,
            DCXLayer.BODY: DCX2_MODEL,
        }
        self._client = httpx.AsyncClient(
            base_url=OLLAMA_BASE_URL,
            timeout=120.0,
        )
        self._available_models: set[str] = set()

    async def connect(self):
        """Check which models are available in Ollama."""
        try:
            resp = await self._client.get("/api/tags")
            if resp.status_code == 200:
                data = resp.json()
                self._available_models = {
                    m["name"] for m in data.get("models", [])
                }
                logger.info("Ollama models available: %s", self._available_models)
            else:
                logger.warning("Ollama responded %s", resp.status_code)
        except Exception as e:
            logger.error("Cannot reach Ollama at %s: %s", OLLAMA_BASE_URL, e)

    @property
    def connected(self) -> bool:
        return len(self._available_models) > 0

    def route(self, query: str) -> DCXLayer:
        """Determine which consciousness layer handles this query."""
        q = query.lower()
        for layer, signals in ROUTING_SIGNALS.items():
            if any(sig in q for sig in signals):
                return layer
        return DCXLayer.MIND  # default

    def _resolve_model(self, layer: DCXLayer) -> str:
        """Find the best available model for a layer."""
        preferred = self._models[layer]
        if preferred in self._available_models:
            return preferred
        # Fallback: use any available model
        if self._available_models:
            fallback = next(iter(self._available_models))
            logger.warning("Model %s not found, falling back to %s", preferred, fallback)
            return fallback
        raise RuntimeError("No Ollama models available")

    async def think(
        self,
        query: str,
        graph_context: list[dict] = None,
        layer: DCXLayer = None,
        conversation_history: list[dict] = None,
    ) -> DCXResponse:
        """Send a query through the appropriate DCX layer."""
        if layer is None:
            layer = self.route(query)

        model = self._resolve_model(layer)
        system = SYSTEM_PROMPTS[layer]

        # Inject graph context
        context_count = 0
        if graph_context:
            context_count = len(graph_context)
            context_block = "\n".join(
                f"- [{c.get('_labels', ['?'])[0] if isinstance(c.get('_labels'), list) else '?'}] "
                f"{c.get('name', c.get('content', c.get('id', '?')))}"
                for c in graph_context[:15]
            )
            system += f"\n\n=== KNOWLEDGE GRAPH CONTEXT ===\n{context_block}\n=== END CONTEXT ==="

        messages = [{"role": "system", "content": system}]
        if conversation_history:
            messages.extend(conversation_history[-10:])  # last 10 turns
        messages.append({"role": "user", "content": query})

        try:
            resp = await self._client.post("/api/chat", json={
                "model": model,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "num_predict": 1024,
                },
            })
            resp.raise_for_status()
            data = resp.json()
            content = data.get("message", {}).get("content", "")
            tokens = data.get("eval_count")

            return DCXResponse(
                layer=layer,
                model=model,
                content=content,
                context_used=context_count,
                tokens=tokens,
            )
        except Exception as e:
            logger.error("DCX %s think failed: %s", layer.value, e)
            return DCXResponse(
                layer=layer,
                model=model,
                content=f"[DCX {layer.value} error: {e}]",
                context_used=context_count,
            )

    async def close(self):
        await self._client.aclose()
