"""Canonical constitutional agent registry (entity.ecosystem)."""
from .ecosystem import AgentDeclaration, AgentNotFound, Ecosystem, GovernanceViolation
from .mind_projector import AGENT_PROJECTION_TEMPLATE, MindProjector, ProjectionResult

__all__ = [
    "AgentDeclaration",
    "AgentNotFound",
    "Ecosystem",
    "GovernanceViolation",
    "AGENT_PROJECTION_TEMPLATE",
    "MindProjector",
    "ProjectionResult",
]
