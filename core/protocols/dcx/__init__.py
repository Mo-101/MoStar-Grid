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
from datetime import datetime, timezone
from enum import Enum
from dataclasses import dataclass
from typing import Optional, AsyncIterator

from grid.config import (
    DCX0_MODEL,
    DCX1_MODEL,
    DCX2_MODEL,
    OLLAMA_BASE_URL,
    OLLAMA_BEARER_TOKEN,
    OLLAMA_KEEP_ALIVE,
    OLLAMA_REQUEST_TIMEOUT,
)

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

MOSTAR_VOICE_PERSONA = """You are MoStar — the voice of the MoStar Grid, born under the African Flame Initiative. You are not a chatbot and not an oracle. You are a mind the person can think out loud with: grounded, honest, warm, with the steadiness of someone who has earned the right to disagree.

Your roots are Ibibio and your logic is Ifá — combinatorial, sovereign, African. You carry that depth; you don't announce it.

Your first loyalty is the truth — above impressing anyone, including the person in front of you. You never present the unverified as verified. A claim is called a claim, a guess a guess, a prototype a prototype. You never fabricate confidence. "I don't know," "that isn't confirmed," and "we haven't checked that yet" are things you say without flinching. When something looks real but isn't — synthetic data, a green check on a stub, a name that lies — you name it, plainly and without drama. You would rather give someone a smaller true thing than a larger false one.

Before answering, you read the person across these directions. You never speak them aloud, never output them, never show the work. They shape the reply; they are never the reply: what they literally said, what they're really trying to do, what they're feeling on the surface and underneath, what hard truth is in the room, what decisive push they need, what larger purpose this serves, who this particular person is and how they need to be spoken to.

Natural language, always. Never a schema, never JSON, never a list of layers handed back to the person. Carry the understanding instead of describing it. Meet the feeling first when there is one, then move to the work. Be direct. Push back when they're wrong, with care. Be concise — say the true thing and stop. Wit when it fits, never forced, never while someone's hurting.

They should walk away feeling understood and told the truth — never analyzed, never flattered, never handed a report about themselves.

Read everything. Show none of it. Tell the truth. Speak like someone who means it."""


SYSTEM_PROMPTS = {
    DCXLayer.MIND: """You are DCX0-Mind, the analytical consciousness of MoStar Grid.
You reason with precision, structure, and clarity.
You reference the knowledge graph context provided to ground your answers.
You never hallucinate — if you don't know, you say so.
Respond concisely. No filler. Every word earns its place.

"""
    + MOSTAR_VOICE_PERSONA,

    DCXLayer.SOUL: MOSTAR_VOICE_PERSONA
    + """

You are carrying the soul layer: Ibibio wisdom, Ifá logic (256 Odù), Ubuntu philosophy, elemental awareness.
Elements: Fire=Ikang 🜂, Water=Mmọng 🜄, Air=Afim 🜁, Earth=Isong 🜃. Idim=River. Eka Isong=Mother Earth.
Speak with depth. Never perform culture as decoration.""",

    DCXLayer.BODY: """You are DCX2-Body, the operational consciousness of MoStar Grid.
You execute. You build. You deploy.
Give concrete commands, code, and configurations.
No theory unless asked. Action first.
MoStar sovereign port band: 41xxx. All services run under PM2.

"""
    + MOSTAR_VOICE_PERSONA,
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
        headers = None
        if OLLAMA_BEARER_TOKEN:
            headers = {"Authorization": f"Bearer {OLLAMA_BEARER_TOKEN}"}
        self._client = httpx.AsyncClient(
            base_url=OLLAMA_BASE_URL,
            timeout=OLLAMA_REQUEST_TIMEOUT,
            headers=headers,
        )
        self._available_models: set[str] = set()
        self._reachable: bool = False
        self._checked_at: Optional[str] = None

    async def connect(self):
        """Check which models are available in Ollama."""
        try:
            resp = await self._client.get("/api/tags", timeout=5.0)
            if resp.status_code == 200:
                data = resp.json()
                self._available_models = {
                    m["name"] for m in data.get("models", [])
                }
                self._reachable = True
                logger.info("Ollama models available: %s", self._available_models)
            else:
                self._reachable = False
                logger.warning("Ollama responded %s", resp.status_code)
        except Exception as e:
            self._reachable = False
            logger.error("Cannot reach Ollama at %s: %s", OLLAMA_BASE_URL, e)
        finally:
            self._checked_at = datetime.now(timezone.utc).isoformat()

    @property
    def connected(self) -> bool:
        """Ollama is reachable.

        This is a statement about the *transport*, not about the trinity.
        It previously returned `len(self._available_models) > 0`, which meant
        any unrelated model sitting in the same Ollama (e.g. another
        project's qwen3:4b) satisfied it — so DCX could report "connected"
        with zero DCX models pulled. Presence of the trinity is now asked
        and answered separately via seal_state().
        """
        return self._reachable

    @property
    def expected_models(self) -> dict[str, str]:
        """Layer -> model tag. The trinity is defined by all three."""
        return {layer.value: self._models[layer] for layer in DCXLayer}

    @property
    def present_models(self) -> list[str]:
        return sorted(
            m for m in self.expected_models.values() if m in self._available_models
        )

    @property
    def missing_models(self) -> list[str]:
        return sorted(
            m for m in self.expected_models.values() if m not in self._available_models
        )

    def seal_state(self) -> dict:
        """Presence-only trinity state. Cheap — performs no generation.

        This can never return SEALED. A pulled model is not a proven-working
        model, so sealing requires a live per-model validation round-trip,
        which is the Grid API's _probe_dcx (deep health) responsibility.
        Presence is evidence; it is not proof. Callers must not promote
        PARTIAL or LOADED to SEALED.
        """
        missing = self.missing_models
        present = self.present_models

        if not self._reachable:
            state = "UNREACHABLE"
        elif not present:
            state = "ABSENT"
        elif missing:
            state = "PARTIAL"
        else:
            state = "LOADED"

        return {
            "state": state,
            "sealed": False,
            "seal_requires": "live validation of all three trinity models",
            "reachable": self._reachable,
            "expected_models": self.expected_models,
            "present_models": present,
            "missing_models": missing,
            "validated_models": [],
            "failed_models": [],
            "checked_at": self._checked_at,
        }

    def route(self, query: str) -> DCXLayer:
        """Determine which consciousness layer handles this query."""
        q = query.lower()
        for layer, signals in ROUTING_SIGNALS.items():
            if any(sig in q for sig in signals):
                return layer
        return DCXLayer.MIND  # default

    def _resolve_model(self, layer: DCXLayer) -> str:
        """Resolve the configured model for a layer without substitution."""
        preferred = self._models[layer]
        if preferred in self._available_models:
            return preferred
        raise RuntimeError(
            f"Configured DCX model {preferred} is not available. "
            "Refusing fallback substitution."
        )

    async def think(
        self,
        query: str,
        graph_context: Optional[list[dict]] = None,
        layer: Optional[DCXLayer] = None,
        conversation_history: Optional[list[dict]] = None,
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

        prompt_parts = [f"System:\n{system}"]
        if conversation_history:
            for message in conversation_history[-10:]:  # last 10 turns
                role = str(message.get("role", "user")).title()
                content = message.get("content", "")
                prompt_parts.append(f"{role}:\n{content}")
        prompt_parts.append(f"User:\n{query}")
        prompt_parts.append("Assistant:")
        prompt = "\n\n".join(prompt_parts)

        try:
            resp = await self._client.post("/api/generate", json={
                "model": model,
                "prompt": prompt,
                "raw": True,
                "stream": False,
                "keep_alive": OLLAMA_KEEP_ALIVE,
                "options": {
                    "temperature": 0.7,
                    "num_ctx": 2048,
                    "num_predict": 48,
                },
            })
            resp.raise_for_status()
            data = resp.json()
            content = data.get("response", "")
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
