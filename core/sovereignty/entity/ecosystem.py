"""Canonical agent registry and constitutional declarations."""
from __future__ import annotations

import csv
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
AGENT_CLASSES = frozenset({"operational", "shadow_agent"})
VISIBILITIES = frozenset({"visible", "shadow"})


def _blank(value: str) -> bool:
    return not value or value.upper() in {"UNKNOWN", "NONE"}


def _split_abilities(value: str) -> tuple[str, ...]:
    if _blank(value):
        return ()
    return tuple(part.strip() for part in value.split(",") if part.strip())


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
    agent_class: str = "operational"
    visibility: str = "visible"

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
        if self.agent_class not in AGENT_CLASSES:
            raise GovernanceViolation(f"invalid agent_class: {self.agent_class}")
        if self.visibility not in VISIBILITIES:
            raise GovernanceViolation(f"invalid visibility: {self.visibility}")

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
            "agent_class": self.agent_class,
            "visibility": self.visibility,
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
            agent_class=str(data.get("agent_class", "operational")),
            visibility=str(data.get("visibility", "visible")),
        )

    @classmethod
    def from_csv_row(cls, row: dict[str, str]) -> "AgentDeclaration":
        """Derive a canonical declaration from an entity_ecosystem.csv row.

        Missing/UNKNOWN values are filled with conservative defaults.
        This is mechanical mapping only; it does not invent doctrine.
        """
        entity_id = row["entity_id"].strip()
        name = row["name"].strip()
        agent_class = row.get("agent_class", "operational").strip()
        visibility = row.get("visibility", "visible").strip()

        role = row.get("role", "").strip() or name
        essence = row.get("essence", "shadow").strip()
        element = essence if essence in ELEMENTS else "shadow"

        owner = row.get("origin", "").strip() if not _blank(row.get("origin")) else "canonical_pantheon"

        raw_attestor = row.get("bonded_to", "").strip()
        attested_by = raw_attestor if not _blank(raw_attestor) else "canonical_pantheon"

        raw_origin = row.get("origin", "").strip()
        origin_model = raw_origin if not _blank(raw_origin) else f"origin:{entity_id}"

        # Enforce independence even when defaults collide.
        if attested_by == origin_model:
            attested_by = "canonical_pantheon"

        truth_threshold = 0.0
        provenance = "authored" if agent_class == "shadow_agent" else "detected"

        abilities = _split_abilities(row.get("abilities", ""))
        if agent_class == "shadow_agent":
            # Breda does not get agent.execute.
            perms = ["provenance.witness" if a == "witness_provenance" else a for a in abilities]
            permissions = tuple(perms) or ("provenance.witness",)
        else:
            permissions = abilities + ("agent.execute",)

        return cls(
            id=entity_id,
            role=role,
            permissions=permissions,
            element=element,
            owner=owner,
            truth_threshold=truth_threshold,
            provenance=provenance,
            attested_by=attested_by,
            origin_model=origin_model,
            agent_class=agent_class,
            visibility=visibility,
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

    @classmethod
    def from_csv(cls, csv_path: pathlib.Path | str) -> "Ecosystem":
        """Load canonical agent declarations from entity_ecosystem.csv."""
        inst = cls()
        with open(csv_path, "r", encoding="utf-8", newline="") as f:
            for row in csv.DictReader(f):
                if not row.get("entity_id", "").strip():
                    continue
                try:
                    declaration = AgentDeclaration.from_csv_row(row)
                except GovernanceViolation:
                    # Fail closed: skip malformed rows.
                    continue
                inst.register(declaration)
        return inst

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
