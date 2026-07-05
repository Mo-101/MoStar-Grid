"""
MoStar MCP Server — Sovereign Runtime Interface
Exposes the Grid as a typed, policy-bounded MCP surface.

Tools call the Broker (Grid API at :41010). No privileged logic executes here.

Transport modes:
  stdio  — default; Claude Code / Claude Desktop integration
  sse    — HTTP SSE server; set MCP_TRANSPORT=sse for PM2 / uvicorn deployment

PM2 (SSE via uvicorn):
  uvicorn mcp_gateway.server:app --host 0.0.0.0 --port 41020

Claude Code (stdio):
  Register in .claude/settings.json mcpServers block.
"""
import asyncio
import json
import os
import sys
import uuid
from datetime import datetime, timezone
from typing import Literal

from mcp.server.fastmcp import FastMCP

from mcp_gateway.broker_client import grid_get, grid_post
from mcp_gateway.config import MCP_HOST, MCP_PORT, MCP_TRANSPORT, GRID_API_URL

_SCRIPTS_DIR = os.path.join(
    os.path.dirname(__file__), "..", "..", "..", "core", "ops", "scripts"
)
_DCX_PROBE = os.path.normpath(os.path.join(_SCRIPTS_DIR, "dcx_readiness.py"))

# ── Server ──────────────────────────────────────────────────────────────────

mcp = FastMCP(
    "MoStar Sovereign Runtime",
    instructions=(
        "You are connected to the MoStar sovereign AI runtime. "
        "All privileged actions go through the Execution Broker (Grid API at port 41010). "
        "Tools here never bypass the policy kernel. "
        "Use propose_action for any write or execute operation. "
        "Use think for local model inference — no external egress. "
        "Use simulate_policy_decision before proposing uncertain actions."
    ),
)

# ── MVP Policy Kernel (local simulation) ────────────────────────────────────
# Compiled from covenant_protection_v1 rule bundle.
# When the full Policy Kernel service is live, swap _simulate_policy for an HTTP call.

_ACTION_TAXONOMY: dict[str, dict] = {
    "READ_PUBLIC":       {"sensitivity": "LOW",      "decision": "ALLOW",            "risk": 0.1,  "obligations": []},
    "READ_SENSITIVE":    {"sensitivity": "MEDIUM",   "decision": "ALLOW",            "risk": 0.3,  "obligations": ["LOG_ACCESS"]},
    "WRITE_METADATA":    {"sensitivity": "MEDIUM",   "decision": "ALLOW",            "risk": 0.3,  "obligations": ["LOG_SIDE_EFFECTS"]},
    "WRITE_OPERATIONAL": {"sensitivity": "HIGH",     "decision": "REQUIRE_APPROVAL", "risk": 0.6,  "obligations": ["LOG_SIDE_EFFECTS", "REQUIRE_JUSTIFICATION"]},
    "EXECUTE_WORKFLOW":  {"sensitivity": "HIGH",     "decision": "ALLOW",            "risk": 0.5,  "obligations": ["LOG_SIDE_EFFECTS", "SANDBOX_REQUIRED"]},
    "EXECUTE_COMMAND":   {"sensitivity": "CRITICAL", "decision": "DENY",             "risk": 1.0,  "obligations": []},
    "CALL_MODEL":        {"sensitivity": "MEDIUM",   "decision": "ALLOW",            "risk": 0.2,  "obligations": ["LOG_MODEL_REF"]},
    "CALL_EXTERNAL":     {"sensitivity": "HIGH",     "decision": "REQUIRE_APPROVAL", "risk": 0.7,  "obligations": ["NO_SENSITIVE_PAYLOAD", "LOG_EGRESS"]},
    "EXPORT_DATA":       {"sensitivity": "CRITICAL", "decision": "REQUIRE_APPROVAL", "risk": 0.9,  "obligations": ["LOG_SIDE_EFFECTS", "REQUIRE_JUSTIFICATION"]},
    "MODIFY_POLICY":     {"sensitivity": "CRITICAL", "decision": "REQUIRE_APPROVAL", "risk": 0.95, "obligations": ["REQUIRE_JUSTIFICATION", "LOG_SIDE_EFFECTS"]},
}

ActionClass = Literal[
    "READ_PUBLIC", "READ_SENSITIVE", "WRITE_METADATA", "WRITE_OPERATIONAL",
    "EXECUTE_WORKFLOW", "EXECUTE_COMMAND", "CALL_MODEL", "CALL_EXTERNAL",
    "EXPORT_DATA", "MODIFY_POLICY",
]


def _simulate_policy(
    action_class: str,
    actor_scopes: list[str],
    no_external_egress: bool,
    declared_purpose: str,
) -> dict:
    taxonomy = _ACTION_TAXONOMY.get(action_class)
    if not taxonomy:
        return {
            "decision": "DENY",
            "risk_score": 1.0,
            "sensitivity": "CRITICAL",
            "reasons": [f"Unknown action class: {action_class!r}. Must be one of: {', '.join(_ACTION_TAXONOMY)}"],
            "obligations": [],
            "applied_policy": "covenant_protection_v1",
            "decision_id": f"dec_{uuid.uuid4().hex[:12]}",
            "evaluated_at": datetime.now(timezone.utc).isoformat(),
        }

    decision = taxonomy["decision"]
    risk = taxonomy["risk"]
    reasons: list[str] = []
    obligations: list[str] = list(taxonomy["obligations"])

    # Rule: deny_unscoped_write — privileged write/execute without scope binding
    if action_class in ("WRITE_OPERATIONAL", "EXECUTE_COMMAND"):
        bound = any(s.startswith(("write:", "execute:")) for s in actor_scopes)
        if not bound:
            decision = "DENY"
            risk = max(risk, 0.8)
            reasons.append("Privileged operation without scope binding [deny_unscoped_write]")

    # Rule: EXECUTE_COMMAND is always denied in the main runtime
    if action_class == "EXECUTE_COMMAND" and decision != "DENY":
        decision = "DENY"
        risk = 1.0
        reasons.append("Arbitrary command execution is prohibited in the main runtime")

    # Rule: deny_external_egress_untrusted — egress denied by caller constraint
    if action_class == "CALL_EXTERNAL" and no_external_egress:
        decision = "DENY"
        risk = max(risk, 0.9)
        reasons.append("External egress denied by caller constraint [deny_external_egress_untrusted]")

    # Risk uplift: sensitive action without declared purpose
    if taxonomy["sensitivity"] in ("HIGH", "CRITICAL") and not declared_purpose.strip():
        risk = min(risk + 0.1, 1.0)
        reasons.append("Sensitive action submitted without declared purpose — risk elevated")

    if not reasons:
        reasons.append(
            f"Action class {action_class!r} evaluated as {decision} under covenant_protection_v1"
        )

    return {
        "decision": decision,
        "risk_score": round(risk, 2),
        "sensitivity": taxonomy["sensitivity"],
        "reasons": reasons,
        "obligations": obligations,
        "applied_policy": "covenant_protection_v1",
        "decision_id": f"dec_{uuid.uuid4().hex[:12]}",
        "evaluated_at": datetime.now(timezone.utc).isoformat(),
    }


# ── Tools ────────────────────────────────────────────────────────────────────

@mcp.tool()
async def simulate_policy_decision(
    action_class: str,
    actor_scopes: list[str],
    purpose: str = "",
    no_external_egress: bool = True,
) -> str:
    """
    Evaluate an action against the MoStar policy taxonomy without executing it.
    Returns decision (ALLOW / DENY / REQUIRE_APPROVAL), risk score, and obligations.

    This is the MVP Policy Kernel running locally. When the full Policy Kernel
    service is live, this tool will proxy to it instead.

    Args:
        action_class: One of READ_PUBLIC, READ_SENSITIVE, WRITE_METADATA,
            WRITE_OPERATIONAL, EXECUTE_WORKFLOW, EXECUTE_COMMAND, CALL_MODEL,
            CALL_EXTERNAL, EXPORT_DATA, MODIFY_POLICY.
        actor_scopes: Scopes the actor holds (e.g. ["read:graph", "model:invoke"]).
        purpose: Declared intent for this action.
        no_external_egress: True if the caller asserts no external network calls.
    """
    result = _simulate_policy(action_class, actor_scopes, no_external_egress, purpose)
    return json.dumps(result, indent=2)


@mcp.tool()
async def propose_action(
    canon_input: str,
    justification: str = "",
) -> str:
    """
    Submit a privileged action proposal to the Grid Broker for policy evaluation.
    The cluster evaluates and either commits, queues for approval, or rejects.
    This is the front door for all write and execute operations.

    Args:
        canon_input: Canonical action description or JSON payload.
        justification: Reason for this action. Required for HIGH/CRITICAL sensitivity.
    """
    body: dict = {"canon_input": canon_input}
    if justification:
        body["justification"] = justification
    result = await grid_post("/api/propose", body)
    return json.dumps(result)


@mcp.tool()
async def get_proposals(proposal_id: str = "") -> str:
    """
    List pending proposals in the execution queue, or fetch a specific one.

    Args:
        proposal_id: If provided, returns that specific proposal. Otherwise lists all.
    """
    if proposal_id:
        result = await grid_get(f"/api/proposals/{proposal_id}")
    else:
        result = await grid_get("/api/proposals")
    return json.dumps(result)


@mcp.tool()
async def approve_proposal(proposal_id: str, rationale: str = "") -> str:
    """
    Approve a pending proposal. Operator-level action — requires execute permission.

    Args:
        proposal_id: The proposal to approve.
        rationale: Operator rationale for the approval.
    """
    body: dict = {"proposal_id": proposal_id}
    if rationale:
        body["rationale"] = rationale
    result = await grid_post("/api/approve", body)
    return json.dumps(result)


@mcp.tool()
async def commit_proposal(proposal_id: str) -> str:
    """
    Commit an approved proposal to execution.

    Args:
        proposal_id: The approved proposal ID to commit.
    """
    result = await grid_post("/api/commit", {"proposal_id": proposal_id})
    return json.dumps(result)


@mcp.tool()
async def reject_proposal(proposal_id: str, reason: str) -> str:
    """
    Reject a proposal and remove it from the execution queue.

    Args:
        proposal_id: The proposal to reject.
        reason: Rejection reason (required — goes into the audit event).
    """
    result = await grid_post("/api/reject", {"proposal_id": proposal_id, "reason": reason})
    return json.dumps(result)


@mcp.tool()
async def think(
    prompt: str,
    model: str = "",
    system_context: str = "",
) -> str:
    """
    Route a reasoning prompt to the local sovereign model (Ollama / DCX layer).
    No external egress. Execution stays within the Grid node.

    Args:
        prompt: The prompt or question to reason over.
        model: Optional model override. Defaults to DCX0 (configured in .env).
        system_context: Optional system-level context to prepend.
    """
    body: dict = {"prompt": prompt}
    if model:
        body["model"] = model
    if system_context:
        body["system_context"] = system_context
    result = await grid_post("/api/think", body)
    return json.dumps(result)


@mcp.tool()
async def check_dcx_readiness() -> str:
    """
    Report DCX earned-readiness from the canonical source: the Grid API health probe.

    This reads the 'dcx' field from /api/health, which is produced by _probe_dcx()
    inside the Grid service — the same probe that drives the Grid's own ready flag.
    One probe, one truth. The MCP tool is a view, not a second opinion.

    States: THINKING (ok=true) | NAKED (model not pulled) | DOWN (unreachable/empty)
    Also surfaces auth_configured so you know whether the bearer token is in play.
    """
    health = await grid_get("/api/health")
    dcx = health.get("dcx", {"state": "ERROR", "reason": "dcx field missing from /api/health"})
    return json.dumps(dcx, indent=2)


@mcp.tool()
async def verify_provenance(limit: int = 20) -> str:
    """
    Retrieve recent provenance events from the audit chain.
    Each event records: what executed, on which node, under which policy decision.

    Args:
        limit: Maximum recent events to return (default 20).
    """
    result = await grid_get("/api/provenance", params={"limit": limit})
    return json.dumps(result)


@mcp.tool()
async def query_mindgraph() -> str:
    """
    Query the Neo4j lineage graph for connectivity status and sentinel node verification.
    Returns: graph health, verified node counts, and sentinel label state.
    """
    result = await grid_get("/api/mindgraph/status")
    return json.dumps(result)


@mcp.tool()
async def get_truthgate_report() -> str:
    """
    Run a TruthGate verification scan across all Grid components.
    Proves operational state from TCP + HTTP evidence — not just configuration claims.

    Five Laws:
      Observed ≠ Inferred | Configured ≠ Running | Declared ≠ Verified
      Available ≠ Proven  | Synthetic State ≠ Public Truth
    """
    result = await grid_get("/api/truthgate/report")
    return json.dumps(result)


@mcp.tool()
async def get_grid_status() -> str:
    """
    Get cluster status: identity, Neo4j connectivity, model availability,
    and orchestrator health.
    Uses /api/health for fast, reliable response. Use query_mindgraph for
    detailed graph census.
    """
    result = await grid_get("/api/health")
    return json.dumps(result)


@mcp.tool()
async def get_telemetry() -> str:
    """
    Get live cluster telemetry: signal density, agent states, recent events,
    and system posture indicators.
    """
    result = await grid_get("/api/telemetry")
    return json.dumps(result)


@mcp.tool()
async def get_agents() -> str:
    """
    List registered agents and their current operational status within the Grid.
    """
    result = await grid_get("/api/agents")
    return json.dumps(result)


@mcp.tool()
async def get_memory(limit: int = 10) -> str:
    """
    Retrieve recent memory entries from the Grid memory layer.

    Args:
        limit: Number of recent entries to return (default 10).
    """
    result = await grid_get("/api/memory/recent", params={"limit": limit})
    return json.dumps(result)


@mcp.tool()
async def get_briefing() -> str:
    """
    Get the current continuity briefing — the Grid's synthesized state summary
    from memory, recent events, and cluster posture.
    """
    result = await grid_get("/api/briefing")
    return json.dumps(result)


@mcp.tool()
async def import_scroll(scroll_url: str, scroll_type: str = "text") -> str:
    """
    Import a scroll (document / evidence artifact) into the Grid knowledge base.

    Args:
        scroll_url: URL or path to the scroll to import.
        scroll_type: Content type hint (default 'text').
    """
    result = await grid_post("/api/scrolls/import", {"url": scroll_url, "type": scroll_type})
    return json.dumps(result)


# ── Resources ────────────────────────────────────────────────────────────────

@mcp.resource("mostar://cluster/status")
async def resource_cluster_status() -> str:
    """Live cluster status snapshot (health endpoint — fast)."""
    result = await grid_get("/api/health")
    return json.dumps(result, indent=2)


@mcp.resource("mostar://proposals/pending")
async def resource_pending_proposals() -> str:
    """Pending proposals awaiting evaluation or operator approval."""
    result = await grid_get("/api/proposals")
    return json.dumps(result, indent=2)


@mcp.resource("mostar://provenance/recent")
async def resource_recent_provenance() -> str:
    """Recent provenance chain — last 50 audit events."""
    result = await grid_get("/api/provenance", params={"limit": 50})
    return json.dumps(result, indent=2)


@mcp.resource("mostar://telemetry/live")
async def resource_live_telemetry() -> str:
    """Live telemetry snapshot from the cluster."""
    result = await grid_get("/api/telemetry")
    return json.dumps(result, indent=2)


@mcp.resource("mostar://registry/entities")
async def resource_entity_registry() -> str:
    """Registered entities in the Grid — agents, nodes, and identity roster."""
    result = await grid_get("/api/grid/startup-reports")
    return json.dumps(result, indent=2)


@mcp.resource("mostar://graph/status")
async def resource_graph_status() -> str:
    """Neo4j lineage graph connectivity and node census."""
    result = await grid_get("/api/mindgraph/status")
    return json.dumps(result, indent=2)


# ── Entrypoints ──────────────────────────────────────────────────────────────

# ASGI app for uvicorn (PM2 / SSE mode):
#   uvicorn mcp_gateway.server:app --host 0.0.0.0 --port 41020
try:
    from starlette.applications import Starlette
    from starlette.routing import Mount, Route
    from starlette.responses import JSONResponse

    async def _health(request):
        """Health endpoint for cockpit/PM2 monitoring."""
        return JSONResponse({
            "status": "ok",
            "service": "mostar-mcp-gateway",
            "port": MCP_PORT,
            "transport": "sse",
            "grid_api_url": GRID_API_URL,
            "tools": len(mcp._tool_manager._tools),
            "resources": len(mcp._resource_manager._resources),
        })

    async def _root(request):
        """Root info endpoint."""
        return JSONResponse({
            "service": "mostar-mcp-gateway",
            "sse_endpoint": "/sse",
            "message_endpoint": "/messages",
            "health": "/health",
            "docs": "Use MCP client (Claude Code, etc.) to connect via SSE",
        })

    _sse_app = mcp.sse_app()
    app = Starlette(
        routes=[
            Route("/health", _health, methods=["GET"]),
            Route("/", _root, methods=["GET"]),
            Mount("/", app=_sse_app),
        ],
    )
except AttributeError:
    app = None  # SSE not available in this mcp version — use stdio mode

if __name__ == "__main__":
    if MCP_TRANSPORT == "sse":
        mcp.run(transport="sse", host=MCP_HOST, port=MCP_PORT)
    else:
        mcp.run()  # stdio — Claude Code / Claude Desktop
