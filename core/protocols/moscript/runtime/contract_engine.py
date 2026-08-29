"""Deterministic governance engine: contracts as law, not eval."""
from __future__ import annotations

import hashlib
import json
import pathlib
import re
from dataclasses import dataclass
from typing import Any, Callable

from entity.ecosystem import AgentDeclaration, AgentNotFound, Ecosystem

from .contract_decision import ContractDecision, GovernanceFailure
from .contract_registry import ContractRegistry, SealedContract


@dataclass(frozen=True)
class CypherTemplate:
    template_id: str
    query: str
    sha256: str


# Deliberately small vocabulary for Cypher-key classification only; no code execution.
_CYPHER_KEYWORDS = {
    "match",
    "return",
    "where",
    "create",
    "merge",
    "delete",
    "detach",
    "remove",
    "drop",
    "set",
    "with",
    "unwind",
    "union",
    "all",
    "limit",
    "skip",
    "order",
    "by",
    "optional",
    "call",
    "yield",
}
_TEMPLATE_ID_PATTERN = re.compile(r"^[a-z0-9-]+$")


def _hash_event(event: dict) -> str:
    canonical = json.dumps(event, sort_keys=True, ensure_ascii=False, default=_json_default)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _json_default(obj: Any) -> Any:
    if isinstance(obj, tuple):
        return list(obj)
    raise TypeError(f"object of type {type(obj).__name__} is not JSON serializable")


def _decision(
    contract_id: str,
    decision: str,
    reason_codes: list[str],
    input_hash: str,
    result: dict[str, Any] | None = None,
) -> ContractDecision:
    return ContractDecision(
        contract_id=contract_id,
        decision=decision,
        reason_codes=tuple(reason_codes),
        input_hash=input_hash,
        result=result or {},
    )


def _eval_attestation(
    engine: GovernanceEngine,
    contract: SealedContract,
    event: dict,
    principal: str,
    context: dict,
    input_hash: str,
) -> ContractDecision:
    origin_model = event.get("origin_model")
    attested_by = event.get("attested_by")
    if origin_model and attested_by and origin_model == attested_by:
        return _decision(
            contract.id,
            "STAGE_CANDIDATE",
            ["SELF_ATTESTATION"],
            input_hash,
            {"candidate_status": "candidate", "target_state": "non_canonical"},
        )
    return _decision(
        contract.id,
        "STAGE_CANDIDATE",
        ["UNCORROBORATED"],
        input_hash,
        {"candidate_status": "candidate", "target_state": "non_canonical"},
    )


def _eval_conduit(
    engine: GovernanceEngine,
    contract: SealedContract,
    event: dict,
    principal: str,
    context: dict,
    input_hash: str,
) -> ContractDecision:
    binding = event.get("binding")
    authority = event.get("authority")
    caller = event.get("caller")
    model_runtime = event.get("model_runtime")

    if not binding or not authority or not model_runtime or not caller:
        return _decision(contract.id, "DENY", ["UNBOUND_INVOCATION"], input_hash)

    if isinstance(binding, dict) and not binding.get("sealed"):
        return _decision(contract.id, "DENY", ["UNBOUND_INVOCATION"], input_hash)
    if isinstance(binding, str) and binding.lower() in {"direct", "bypass"}:
        return _decision(contract.id, "DENY", ["UNBOUND_INVOCATION"], input_hash)

    if isinstance(authority, dict) and not authority.get("approved"):
        return _decision(contract.id, "DENY", ["UNAUTHORIZED_INVOCATION"], input_hash)

    if caller != principal:
        return _decision(contract.id, "DENY", ["CALLER_MISMATCH"], input_hash)

    return _decision(
        contract.id,
        "ALLOW",
        [],
        input_hash,
        {
            "binding": binding,
            "authority": authority,
            "model_runtime": model_runtime,
        },
    )


def _eval_cypher(
    engine: GovernanceEngine,
    contract: SealedContract,
    event: dict,
    principal: str,
    context: dict,
    input_hash: str,
) -> ContractDecision:
    query_key = event.get("query_key", "")
    params = event.get("params", {})

    if not isinstance(query_key, str):
        return _decision(contract.id, "DENY", ["INVALID_QUERY_KEY"], input_hash)

    if not _TEMPLATE_ID_PATTERN.match(query_key):
        lowered = query_key.lower()
        if any(re.search(rf"\b{kw}\b", lowered) for kw in _CYPHER_KEYWORDS):
            return _decision(contract.id, "DENY", ["RAW_CYPHER"], input_hash)
        return _decision(contract.id, "DENY", ["UNKNOWN_TEMPLATE"], input_hash)

    template = engine.cypher_templates.get(query_key)
    if template is None:
        return _decision(contract.id, "DENY", ["UNKNOWN_TEMPLATE"], input_hash)

    actual_hash = hashlib.sha256(template.query.encode("utf-8")).hexdigest()
    if actual_hash != template.sha256:
        return _decision(contract.id, "DENY", ["TAMPERED_TEMPLATE"], input_hash)

    # Parameters are passed separately; the query text is never interpolated.
    return _decision(
        contract.id,
        "ALLOW",
        [],
        input_hash,
        {
            "query": template.query,
            "params": params,
            "template_id": template.template_id,
        },
    )


def _eval_provenance(
    engine: GovernanceEngine,
    contract: SealedContract,
    event: dict,
    principal: str,
    context: dict,
    input_hash: str,
) -> ContractDecision:
    license_status = event.get("license_status")
    consent_status = event.get("consent_status")
    withdrawn = event.get("withdrawn", False)
    derivation_permitted = event.get("derivation_permitted", True)
    inference_purpose = event.get("inference_purpose", context.get("inference_purpose"))
    allowed_purposes = event.get("allowed_purposes", [])

    if not (license_status == "permitted" or event.get("licensed") is True):
        return _decision(contract.id, "FILTER", ["UNLICENSED"], input_hash)

    if consent_status == "denied":
        return _decision(contract.id, "FILTER", ["CONSENT_DENIED"], input_hash)

    if withdrawn:
        return _decision(contract.id, "FILTER", ["WITHDRAWN"], input_hash)

    if not derivation_permitted and inference_purpose not in allowed_purposes:
        return _decision(contract.id, "FILTER", ["DERIVATION_LIMITED"], input_hash)

    return _decision(contract.id, "ALLOW", [], input_hash)


_COMPILED_CONTRACTS: dict[str, Callable] = {
    "mo-mind-attestation-guard-001": _eval_attestation,
    "mo-mind-conduit-001": _eval_conduit,
    "mo-mind-cypher-guard-001": _eval_cypher,
    "mo-mind-provenance-filter-001": _eval_provenance,
}


class GovernanceEngine:
    """Evaluate MoMind governance contracts at runtime boundaries."""

    def __init__(self, registry: ContractRegistry | None = None):
        self.registry = registry or ContractRegistry()
        self.cypher_templates: dict[str, CypherTemplate] = {}

    @classmethod
    def from_path(cls, contracts_dir: pathlib.Path | str) -> "GovernanceEngine":
        registry = ContractRegistry.from_path(contracts_dir)
        return cls(registry)

    def load_and_freeze(self, contracts_dir: pathlib.Path | str):
        self.registry.load_and_freeze(contracts_dir)

    @property
    def ready(self) -> bool:
        return self.registry.ready

    def register_cypher_template(
        self,
        template_id: str,
        query: str,
        expected_hash: str | None = None,
    ) -> None:
        actual_hash = hashlib.sha256(query.encode("utf-8")).hexdigest()
        stored_hash = expected_hash if expected_hash is not None else actual_hash
        self.cypher_templates[template_id] = CypherTemplate(
            template_id=template_id,
            query=query,
            sha256=stored_hash,
        )

    def evaluate(
        self,
        contract_id: str,
        event: dict,
        *,
        principal: str,
        context: dict | None = None,
    ) -> ContractDecision:
        if not self.registry.ready:
            raise GovernanceFailure("governance engine is not ready")
        contract = self.registry.get(contract_id)
        context = context or {}
        input_hash = _hash_event(event)
        compiled = _COMPILED_CONTRACTS.get(contract_id)
        if compiled is None:
            raise GovernanceFailure(f"no compiled evaluator for {contract_id}")
        return compiled(self, contract, event, principal, context, input_hash)

    def govern(
        self,
        agent_id: str,
        action: str,
        *,
        ecosystem: Ecosystem,
        context: dict | None = None,
    ) -> ContractDecision:
        """Fail-closed agent action evaluation against the canonical ecosystem."""
        context = context or {}
        contract_id = "entity.agent.execution"
        event = {"agent_id": agent_id, "action": action}

        if ecosystem is None:
            return _decision(contract_id, "DENY", ["MISSING_ECOSYSTEM"], _hash_event(event))

        try:
            agent = ecosystem.require_agent(agent_id)
        except AgentNotFound:
            return _decision(
                contract_id,
                "DENY",
                ["UNKNOWN_AGENT"],
                _hash_event(event),
            )

        try:
            # Re-validate the declaration at enforcement time.
            AgentDeclaration(**agent.to_dict())
        except Exception as exc:
            return _decision(
                contract_id,
                "DENY",
                ["INVALID_DECLARATION"],
                _hash_event(agent.to_dict()),
            )

        if not agent.has_permission(action):
            return _decision(
                contract_id,
                "DENY",
                ["PERMISSION_DENIED"],
                _hash_event(agent.to_dict()),
            )

        truth_score = context.get("truth_score", 1.0)
        if truth_score < agent.truth_threshold:
            return _decision(
                contract_id,
                "DENY",
                ["TRUTH_THRESHOLD"],
                _hash_event(agent.to_dict()),
            )

        return _decision(
            contract_id,
            "ALLOW",
            [],
            _hash_event(agent.to_dict()),
            {"agent_id": agent.id, "role": agent.role, "owner": agent.owner},
        )
