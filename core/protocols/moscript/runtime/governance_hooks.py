"""Grid-op boundary hooks that wrap the governance engine."""
from __future__ import annotations

from typing import Any

from .contract_decision import ContractDecision, GovernanceFailure
from .contract_engine import GovernanceEngine


class MoMindConduit:
    """Enforces `mo-mind-conduit-001` before every model invocation."""

    def __init__(self, engine: GovernanceEngine):
        self._engine = engine

    def invoke(self, request: dict, principal: str, **context) -> ContractDecision:
        decision = self._engine.evaluate(
            "mo-mind-conduit-001",
            request,
            principal=principal,
            context=context,
        )
        if decision.decision != "ALLOW":
            raise GovernanceFailure(
                f"model invocation denied: {decision.reason_codes}"
            )
        return decision


class AttestationGuard:
    """Enforces `mo-mind-attestation-guard-001` after model output."""

    def __init__(self, engine: GovernanceEngine):
        self._engine = engine

    def stage(self, claim: dict, principal: str) -> ContractDecision:
        return self._engine.evaluate(
            "mo-mind-attestation-guard-001",
            claim,
            principal=principal,
        )


class ProvenanceFilter:
    """Enforces `mo-mind-provenance-filter-001` per memory item."""

    def __init__(self, engine: GovernanceEngine):
        self._engine = engine

    def filter(self, memory: dict, principal: str, inference_purpose: str) -> ContractDecision:
        event = dict(memory)
        event["inference_purpose"] = inference_purpose
        return self._engine.evaluate(
            "mo-mind-provenance-filter-001",
            event,
            principal=principal,
        )


class CypherGuardAdapter:
    """Enforces `mo-mind-cypher-guard-001` before any graph query."""

    def __init__(self, engine: GovernanceEngine):
        self._engine = engine

    def run_template(
        self,
        query_key: str,
        params: dict,
        request_origin: str,
        principal: str,
    ) -> ContractDecision:
        return self._engine.evaluate(
            "mo-mind-cypher-guard-001",
            {
                "query_key": query_key,
                "params": params,
                "request_origin": request_origin,
            },
            principal=principal,
        )
