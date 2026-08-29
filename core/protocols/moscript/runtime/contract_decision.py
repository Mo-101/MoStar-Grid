"""Structured governance decision object."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

VALID_DECISIONS = frozenset({"ALLOW", "DENY", "FILTER", "STAGE_CANDIDATE", "QUARANTINE", "ERROR"})


class GovernanceFailure(RuntimeError):
    """Raised when a governance boundary fails closed."""


@dataclass(frozen=True)
class ContractDecision:
    contract_id: str
    decision: str
    reason_codes: tuple[str, ...] = ()
    input_hash: str = ""
    result: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if self.decision not in VALID_DECISIONS:
            raise ValueError(f"invalid decision {self.decision!r}")

    @property
    def allowed(self) -> bool:
        return self.decision == "ALLOW"

    def to_dict(self) -> dict[str, Any]:
        return {
            "contract_id": self.contract_id,
            "decision": self.decision,
            "reason_codes": list(self.reason_codes),
            "input_hash": self.input_hash,
            "result": self.result,
        }
