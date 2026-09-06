"""Universal backend Mind Conduit capability and governed runtime adapter."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Awaitable, Callable, TypeVar

from grid.canonical_evidence import load_mind_conduit_status

T = TypeVar("T")
_CAPABILITY = object()
OLLAMA_GENERATE_PATH = "/api/generate"
OLLAMA_CHAT_PATH = "/api/chat"


@dataclass(frozen=True)
class GridModelInvocationContext:
    model_id: str
    binding_identity: str
    snapshot_identity: str
    caller: str
    _capability: object

    def assert_valid(self) -> None:
        if self._capability is not _CAPABILITY:
            raise RuntimeError("DIRECT_MODEL_INVOCATION_FORBIDDEN")


async def invoke_model(
    *,
    caller: str,
    model_id: str,
    snapshot_identity: str,
    adapter: Callable[[GridModelInvocationContext], Awaitable[T]],
) -> T:
    evidence = load_mind_conduit_status()
    if not evidence["GRID_MIND_READY"]:
        raise RuntimeError("MIND_CONDUIT_NOT_SEALED")
    context = GridModelInvocationContext(
        model_id=model_id,
        binding_identity=evidence["constitution_hash_lineage"]["current_hash"],
        snapshot_identity=snapshot_identity,
        caller=caller,
        _capability=_CAPABILITY,
    )
    return await adapter(context)


async def governed_http_post(
    context: GridModelInvocationContext,
    client: Any,
    path: str,
    payload: dict,
):
    context.assert_valid()
    if path not in {OLLAMA_GENERATE_PATH, OLLAMA_CHAT_PATH, "/v1/chat/completions", "/v1/responses", "/v1/embeddings"}:
        raise RuntimeError("UNREGISTERED_MODEL_TRANSPORT_PATH")
    return await client.post(path, json=payload)


async def invoke_dcx(context: GridModelInvocationContext, dcx: Any, **kwargs):
    context.assert_valid()
    return await dcx.think(invocation_context=context, **kwargs)
