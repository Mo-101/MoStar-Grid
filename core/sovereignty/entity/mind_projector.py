"""MindProjector: project canonical AgentDeclarations into the Neo4j Mind.

This is a host-side adapter behind the future `graph.template.execute` MoScript
capability. It does not decide canonicality; it consumes declarations already
resolved by the canonical Ecosystem and bound to the `mo-mind-cypher-guard-001`
sealed template.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from moscript.runtime import GovernanceEngine

from .ecosystem import AgentNotFound, Ecosystem


AGENT_PROJECTION_TEMPLATE = """
MERGE (a:Agent {id: $entity_id, canonical: $canonical})
ON CREATE SET
  a.name = $name,
  a.role = $role,
  a.agent_class = $agent_class,
  a.visibility = $visibility,
  a.element = $element,
  a.provenance = $provenance,
  a.attested_by = $attested_by,
  a.origin_model = $origin_model,
  a.permissions = $permissions,
  a.canonical = $canonical
ON MATCH SET
  a.canonical = $canonical,
  a.name = $name,
  a.role = $role,
  a.agent_class = $agent_class,
  a.visibility = $visibility,
  a.element = $element,
  a.provenance = $provenance,
  a.attested_by = $attested_by,
  a.origin_model = $origin_model,
  a.permissions = $permissions
RETURN a
""".strip()


@dataclass
class ProjectionResult:
    entity_id: str
    status: str
    query: str | None = None
    params: dict[str, Any] | None = None
    node: Any | None = None
    reason_codes: list[str] | None = None
    reason: str | None = None

    @property
    def allowed(self) -> bool:
        return self.status == "PROJECTED"


class MindProjector:
    """Project canonical agents into the Neo4j Mind via a sealed Cypher template."""

    TEMPLATE_ID = "agent-projection-001"

    def __init__(self, ecosystem: Ecosystem, engine: GovernanceEngine):
        self.ecosystem = ecosystem
        self.engine = engine
        self.engine.register_cypher_template(
            self.TEMPLATE_ID,
            AGENT_PROJECTION_TEMPLATE,
        )

    def _declaration_params(self, declaration) -> dict[str, Any]:
        return {
            "entity_id": declaration.id,
            "name": declaration.id,  # canonical display name is the entity_id
            "role": declaration.role,
            "agent_class": declaration.agent_class,
            "visibility": declaration.visibility,
            "element": declaration.element,
            "provenance": declaration.provenance,
            "attested_by": declaration.attested_by,
            "origin_model": declaration.origin_model,
            "permissions": list(declaration.permissions),
            "canonical": True,
        }

    def project(self, entity_id: str, driver=None) -> ProjectionResult:
        """Project a single canonical entity into the graph.

        Returns PROJECTED if the driver executes the sealed query.
        Returns READY if no driver is supplied (query validated but not run).
        Returns DENY for unknown or non-canonical entities.
        Returns HELD if the Cypher guard denies the template request.
        """
        try:
            declaration = self.ecosystem.require_agent(entity_id)
        except AgentNotFound:
            return ProjectionResult(
                entity_id=entity_id,
                status="DENY",
                reason="entity is not canonical",
                reason_codes=["UNKNOWN_AGENT"],
            )

        # Breda must not gain execution authority through projection.
        if declaration.agent_class == "shadow_agent" and declaration.has_permission("agent.execute"):
            return ProjectionResult(
                entity_id=entity_id,
                status="DENY",
                reason="shadow agent must not hold agent.execute",
                reason_codes=["SHADOW_EXECUTION"],
            )

        params = self._declaration_params(declaration)
        dec = self.engine.evaluate(
            "mo-mind-cypher-guard-001",
            {
                "query_key": self.TEMPLATE_ID,
                "params": params,
                "request_origin": "mind",
            },
            principal="mind-projector",
        )

        if dec.decision != "ALLOW":
            return ProjectionResult(
                entity_id=entity_id,
                status="HELD",
                reason=f"cypher guard: {dec.reason_codes}",
                reason_codes=list(dec.reason_codes),
            )

        query = dec.result["query"]

        if driver is None:
            return ProjectionResult(
                entity_id=entity_id,
                status="READY",
                query=query,
                params=params,
            )

        try:
            with driver.session() as session:
                record = session.run(query, params).single()
                node = record["a"] if record else None
                return ProjectionResult(
                    entity_id=entity_id,
                    status="PROJECTED",
                    query=query,
                    params=params,
                    node=node,
                )
        except Exception as exc:  # pragma: no cover - driver/Neo4j failures
            return ProjectionResult(
                entity_id=entity_id,
                status="FAILED",
                query=query,
                params=params,
                reason=str(exc),
                reason_codes=["GRAPH_FAILURE"],
            )

    def project_all(self, driver=None) -> dict[str, ProjectionResult]:
        """Project every canonical agent and return per-entity results."""
        return {
            entity_id: self.project(entity_id, driver=driver)
            for entity_id in self.ecosystem.ids()
        }
