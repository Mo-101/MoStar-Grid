"""Canonical agent registry and constitutional declarations."""
from __future__ import annotations

import json
import pathlib
from dataclasses import asdict, dataclass
from typing import Any


class GovernanceViolation(ValueError):
    """Raised when an agent declaration violates a constitutional rule."""


class AgentNotFound(KeyError):
    """Raised when an agent is not present in the ecosystem registry."""


ELEMENTS = frozenset({"ikang", "mmong", "afim", "isong", "shadow"})
PROVENANCE = frozenset({"authored", "detected", "derived"})


@dataclass(frozen=True)
class AgentDeclaration:
    """A constitutional agent that must be registered before it can act."""

    id: str
    role: str
    permissions: tuple[str, ...]
    element: str
    owner: str
    truth_threshold: float
    provenance: str
    attested_by: str
    origin_model: str

    def __post_init__(self):
        if not self.id:
            raise GovernanceViolation("agent id is required")
        if not self.role:
            raise GovernanceViolation("agent role is required")
        if not self.owner:
            raise GovernanceViolation("agent owner is required")
        if not self.attested_by:
            raise GovernanceViolation("agent attested_by is required")
        if not self.origin_model:
            raise GovernanceViolation("agent origin_model is required")
        if self.attested_by == self.origin_model:
            raise GovernanceViolation("attested_by may not equal origin_model")
        if self.element not in ELEMENTS:
            raise GovernanceViolation(f"invalid element: {self.element}")
        if self.provenance not in PROVENANCE:
            raise GovernanceViolation(f"invalid provenance: {self.provenance}")
        if not (0.0 <= self.truth_threshold <= 1.0):
            raise GovernanceViolation("truth_threshold must be between 0.0 and 1.0")
        if not self.permissions or not all(isinstance(p, str) and p for p in self.permissions):
            raise GovernanceViolation("permissions must be a non-empty list of strings")

    def has_permission(self, action: str) -> bool:
        return action in self.permissions or "*" in self.permissions

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "role": self.role,
            "permissions": list(self.permissions),
            "element": self.element,
            "owner": self.owner,
            "truth_threshold": self.truth_threshold,
            "provenance": self.provenance,
            "attested_by": self.attested_by,
            "origin_model": self.origin_model,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AgentDeclaration":
        return cls(
            id=str(data["id"]),
            role=str(data["role"]),
            permissions=tuple(str(p) for p in data.get("permissions", [])),
            element=str(data.get("element", "shadow")),
            owner=str(data["owner"]),
            truth_threshold=float(data.get("truth_threshold", 0.0)),
            provenance=str(data.get("provenance", "detected")),
            attested_by=str(data["attested_by"]),
            origin_model=str(data["origin_model"]),
        )


class Ecosystem:
    """Canonical in-memory and optionally persisted agent registry."""

    def __init__(self, registry_path: pathlib.Path | str | None = None):
        self._agents: dict[str, AgentDeclaration] = {}
        self._registry_path: pathlib.Path | None = None
        if registry_path is not None:
            self._registry_path = pathlib.Path(registry_path)
            self._load()

    @classmethod
    def in_memory(cls) -> "Ecosystem":
        return cls()

    def _load(self) -> None:
        if self._registry_path is None or not self._registry_path.exists():
            return
        data = json.loads(self._registry_path.read_text(encoding="utf-8"))
        for item in data.get("agents", []):
            try:
                agent = AgentDeclaration.from_dict(item)
            except GovernanceViolation:
                # Fail closed: skip malformed declarations on load.
                continue
            self._agents[agent.id] = agent

    def save(self) -> None:
        if self._registry_path is None:
            return
        self._registry_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"agents": [a.to_dict() for a in self._agents.values()]}
        self._registry_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def register(self, declaration: AgentDeclaration) -> None:
        """Register an agent in the canonical ecosystem."""
        self._agents[declaration.id] = declaration

    def require_agent(self, agent_id: str) -> AgentDeclaration:
        if agent_id not in self._agents:
            raise AgentNotFound(f"agent {agent_id} not in ecosystem")
        return self._agents[agent_id]

    def get(self, agent_id: str) -> AgentDeclaration | None:
        return self._agents.get(agent_id)

    def ids(self) -> list[str]:
        return list(self._agents.keys())

    def to_dict(self) -> dict[str, Any]:
        return {"agents": [a.to_dict() for a in self._agents.values()]}
