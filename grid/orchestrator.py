"""
Grid Orchestrator — The Living Intelligence
Ties MindGraph, DCX Trinity, Truth Engine, Woo, MoScript, and Provenance
into the Talk → Learn → Remember loop.

This is where the Grid breathes.
"""
import logging
import uuid
from datetime import datetime, timezone
from dataclasses import dataclass, field, asdict

from mindgraph import MindGraph
from dcx import DCXTrinity, DCXLayer
from truth_engine import TruthEngine
from woo import WooGate, WooInterpreter
from moscript import MoScriptEngine
from provenance import ProvenanceLog
from soul import SoulPrint
from grid.config import MOSTAR_CLUSTER_ID, SEAL_GLYPH, cluster_metadata, ensure_cluster_dirs
from approval_queue import ApprovalQueue, ProposalRecord, ProposalState, new_proposal_id
from decision_engine import DecisionEngine
from density_telemetry import DensityTelemetry
from federation.scrolls import SCROLL_VERSION

logger = logging.getLogger("orchestrator")


@dataclass
class GridResponse:
    """Complete response from one intelligence cycle."""
    cycle_id: str
    query: str
    response: str
    dcx_layer: str
    dcx_model: str
    context_nodes: int
    truth_passed: bool
    truth_scores: dict
    woo_approved: bool
    sealed: bool
    seal: str = ""
    moment_id: str = ""
    memory_id: str = ""
    moscript_events: list = field(default_factory=list)
    error: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class CommitResult:
    proposal_id: str
    cluster_id: str
    state: str
    memory_id: str
    moment_id: str
    committed_at: str
    seal: str
    scroll_version: str = SCROLL_VERSION

    def to_dict(self) -> dict:
        return asdict(self)


class CommitForbiddenError(RuntimeError):
    pass


class CommitFailedError(RuntimeError):
    pass


class GridOrchestrator:
    """
    The sovereign intelligence loop.
    
    Talk  → Receive query, retrieve graph context, route to DCX
    Learn → Extract knowledge from the exchange, write to graph
    Remember → Stamp a MoStarMoment, seal the cycle
    """

    def __init__(self):
        self.mindgraph = MindGraph()
        self.dcx = DCXTrinity()
        self.truth = TruthEngine()
        self.woo = WooGate()
        self.woo_interpreter = WooInterpreter()
        self.moscript = MoScriptEngine()
        self.provenance = ProvenanceLog()
        self.soul = SoulPrint()
        self.approval_queue = ApprovalQueue()
        self.decision_engine = DecisionEngine()
        self.density = DensityTelemetry(self.mindgraph)
        self._conversation_history: list[dict] = []
        self._ready = False

    async def boot(self):
        """Initialize all subsystems."""
        logger.info("Grid booting...")
        ensure_cluster_dirs()

        # Connect MindGraph
        try:
            await self.mindgraph.connect()
            await self.mindgraph.ensure_schema()
        except Exception as e:
            logger.warning("MindGraph boot partial: %s", e)

        # Connect DCX Trinity
        try:
            await self.dcx.connect()
        except Exception as e:
            logger.warning("DCX Trinity boot partial: %s", e)

        # Fire startup MoScripts
        startup_ctx = {
            "neo4j_connected": self.mindgraph.connected,
            "ollama_connected": self.dcx.connected,
            "soul": self.soul.to_dict(),
        }
        startup_events = self.moscript.fire_trigger("on_startup", startup_ctx)

        self._ready = True
        logger.info("Grid ONLINE — MindGraph:%s DCX:%s %s",
                     self.mindgraph.connected, self.dcx.connected, SEAL_GLYPH)
        return {
            "status": "online",
            **cluster_metadata(),
            "mindgraph": self.mindgraph.connected,
            "dcx": self.dcx.connected,
            "soul": self.soul.declare(),
            "moscript_startup": startup_events,
        }

    async def shutdown(self):
        await self.mindgraph.close()
        await self.dcx.close()
        logger.info("Grid shutdown complete")

    # ── The Loop ───────────────────────────────────────────────────

    async def think(self, query: str, force_layer: DCXLayer = None) -> GridResponse:
        """
        Execute one complete Talk → Learn → Remember cycle.
        """
        raise CommitForbiddenError(
            "think() direct cycles are disabled under Phase 4.0a. Use propose/approve/commit."
        )
        cycle_id = f"cycle_{uuid.uuid4().hex[:12]}"
        logger.info("=== CYCLE %s START ===", cycle_id)

        # ── TALK: Retrieve context and think ──
        graph_context = []
        if self.mindgraph.connected:
            graph_context = await self.mindgraph.retrieve_context(query)

        dcx_response = await self.dcx.think(
            query=query,
            graph_context=graph_context,
            layer=force_layer,
            conversation_history=self._conversation_history,
        )

        # ── TRUTH GATE ──
        truth_verdict = self.truth.evaluate(
            response=dcx_response.content,
            query=query,
            context_count=dcx_response.context_used,
        )

        # ── WOO JUDGMENT ──
        woo_judgment = self.woo.judge(truth_verdict, action_type="response")

        # Fire on_query MoScripts
        query_events = self.moscript.fire_trigger("on_query", {
            "truth_passed": truth_verdict.passed,
            "truth_scores": truth_verdict.scores,
        })

        # ── LEARN: Write knowledge to graph ──
        memory_id = ""
        if self.mindgraph.connected and truth_verdict.passed:
            memory_id = await self.mindgraph.learn(
                category="conversation",
                content=f"Q: {query[:200]} → A: {dcx_response.content[:300]}",
                source=f"dcx:{dcx_response.layer.value}",
                metadata={"cycle_id": cycle_id, "truth_scores": truth_verdict.scores},
            )
            self.moscript.fire_trigger("on_learn", {
                "content": dcx_response.content[:100],
                "category": "conversation",
            })

        # ── REMEMBER: Stamp the moment ──
        moment_id = ""
        if self.mindgraph.connected and truth_verdict.passed and memory_id:
            moment_id = await self.mindgraph.stamp_moment(
                talk_input=query,
                think_output=dcx_response.content,
                memory_id=memory_id,
            )

        # ── PROVENANCE ──
        self.provenance.record(
            cycle_id=cycle_id,
            talk_input=query[:500],
            dcx_layer=dcx_response.layer.value,
            dcx_model=dcx_response.model,
            context_nodes=dcx_response.context_used,
            truth_passed=truth_verdict.passed,
            truth_scores=truth_verdict.scores,
            woo_approved=woo_judgment.approved,
            woo_confidence=woo_judgment.confidence,
            memory_id=memory_id,
            moment_id=moment_id,
        )

        # Update conversation history
        self._conversation_history.append({"role": "user", "content": query})
        self._conversation_history.append({"role": "assistant", "content": dcx_response.content})
        # Keep last 20 turns
        if len(self._conversation_history) > 40:
            self._conversation_history = self._conversation_history[-40:]

        sealed = truth_verdict.passed and bool(moment_id)
        logger.info("=== CYCLE %s %s ===", cycle_id, "SEALED" if sealed else "UNSEALED")

        return GridResponse(
            cycle_id=cycle_id,
            query=query,
            response=dcx_response.content,
            dcx_layer=dcx_response.layer.value,
            dcx_model=dcx_response.model,
            context_nodes=dcx_response.context_used,
            truth_passed=truth_verdict.passed,
            truth_scores=truth_verdict.scores,
            woo_approved=woo_judgment.approved,
            sealed=sealed,
            seal=SEAL_GLYPH if sealed else "",
            moment_id=moment_id,
            memory_id=memory_id,
            moscript_events=query_events,
        )

    # ── Phase 4.0a Assisted Canon Ingestion ─────────────────────────────

    async def interpret(self, canon_input: str) -> dict:
        graph_context = []
        if self.mindgraph.connected:
            graph_context = await self.mindgraph.retrieve_context(canon_input)

        interpretation = await self.woo_interpreter.interpret(canon_input, graph_context)
        proposed_labels = self._labels_for_category(interpretation.category)
        consistency = await self.truth.validate_consistency(
            proposed_content=canon_input,
            proposed_labels=proposed_labels,
            existing_context=graph_context,
        )
        placement = await self.decision_engine.rank_placement(
            interpretation=interpretation,
            existing_context=graph_context,
            consistency_report=consistency,
        )
        return {
            "canon_input": canon_input,
            "context": graph_context,
            "interpretation": interpretation,
            "consistency": consistency,
            "placement": placement,
        }

    async def propose(self, canon_input: str, parent_id: str = None, version: int = 1) -> ProposalRecord:
        interpreted = await self.interpret(canon_input)
        interpretation = interpreted["interpretation"]
        consistency = interpreted["consistency"]
        placement = interpreted["placement"]
        selected = placement.options[placement.selected]
        proposal = ProposalRecord(
            id=new_proposal_id(),
            state=ProposalState.PROPOSED,
            canon_input=canon_input,
            interpretation=interpretation.to_dict(),
            consistency={
                "passed": consistency.passed,
                "scores": consistency.scores,
                "thresholds": consistency.thresholds,
                "failures": consistency.failures,
                "seal": consistency.seal,
            },
            placement=placement.to_dict(),
            proposed_mutations=[
                {
                    "operation": "mindgraph.learn",
                    "cluster_id": MOSTAR_CLUSTER_ID,
                    "category": selected.properties.get("category", "canon"),
                    "content": canon_input,
                    "source": "canon_ingestion",
                    "labels": selected.labels,
                },
                {
                    "operation": "mindgraph.stamp_moment",
                    "cluster_id": MOSTAR_CLUSTER_ID,
                    "talk_input": canon_input,
                    "think_output": interpretation.reasoning,
                },
            ],
            proposed_at=datetime.now(timezone.utc).isoformat(),
            parent_id=parent_id,
            version=version,
        )
        await self.approval_queue.enqueue(proposal)
        self.provenance.record_event("proposal_created", {"proposal_id": proposal.id})
        return proposal

    async def revise(self, proposal_id: str, corrections: str) -> ProposalRecord:
        parent = await self.approval_queue.get(proposal_id)
        if parent.state not in {ProposalState.PROPOSED, ProposalState.REJECTED}:
            raise CommitForbiddenError(
                f"Cannot revise proposal {proposal_id} from state {parent.state.value}"
            )
        parent.state = ProposalState.REVISED
        await self.approval_queue.replace(parent, "revise_parent")
        revised = await self.propose(
            canon_input=corrections,
            parent_id=parent.id,
            version=parent.version + 1,
        )
        self.provenance.record_event(
            "proposal_revised",
            {"proposal_id": revised.id, "parent_id": parent.id},
        )
        return revised

    async def commit_after_seal(self, proposal_id: str) -> CommitResult:
        proposal = await self.approval_queue.get(proposal_id)
        if proposal.state != ProposalState.APPROVED:
            raise CommitForbiddenError("proposal.state must be approved before commit")
        if not proposal.approved_by:
            raise CommitForbiddenError("proposal.approved_by is required before commit")
        if not proposal.approved_at:
            raise CommitForbiddenError("proposal.approved_at is required before commit")
        if not self.mindgraph.connected:
            raise CommitFailedError("MindGraph not connected")

        labels = self._labels_for_category(proposal.interpretation.get("category", "knowledge"))
        context = await self.mindgraph.retrieve_context(proposal.canon_input)
        truth_verdict = await self.truth.validate_consistency(
            proposed_content=proposal.canon_input,
            proposed_labels=labels,
            existing_context=context,
        )
        if not truth_verdict.passed:
            raise CommitForbiddenError(
                f"Commit re-validation failed: {', '.join(truth_verdict.failures)}"
            )

        token = self.mindgraph.begin_commit()
        try:
            memory_id = await self.mindgraph.learn(
                category=proposal.interpretation.get("category", "canon"),
                content=proposal.canon_input,
                source="canon_ingestion",
                metadata={
                    "proposal_id": proposal.id,
                    "approved_by": proposal.approved_by,
                    "cluster_id": MOSTAR_CLUSTER_ID,
                },
                _commit_token=token,
            )
            moment_id = await self.mindgraph.stamp_moment(
                talk_input=proposal.canon_input,
                think_output=proposal.interpretation.get("reasoning", "sealed canon ingestion"),
                memory_id=memory_id,
                _commit_token=token,
            )
        finally:
            self.mindgraph.end_commit(token)

        committed_at = datetime.now(timezone.utc).isoformat()
        proposal.state = ProposalState.COMMITTED
        proposal.committed_at = committed_at
        proposal.memory_id = memory_id
        proposal.moment_id = moment_id
        await self.approval_queue.replace(proposal, "commit")
        self.provenance.record_event(
            "proposal_committed",
            {
                "proposal_id": proposal.id,
                "memory_id": memory_id,
                "moment_id": moment_id,
                "approved_by": proposal.approved_by,
            },
        )
        return CommitResult(
            proposal_id=proposal.id,
            cluster_id=MOSTAR_CLUSTER_ID,
            state=proposal.state.value,
            memory_id=memory_id,
            moment_id=moment_id,
            committed_at=committed_at,
            seal=SEAL_GLYPH,
        )

    @staticmethod
    def _labels_for_category(category: str) -> list[str]:
        category = (category or "knowledge").lower()
        if category == "agent":
            return ["Agent", "GridKnowledge"]
        if category == "rollback":
            return ["Rollback", "GridKnowledge"]
        return ["Memory", "GridKnowledge"]

    # ── Status ─────────────────────────────────────────────────────

    async def status(self) -> dict:
        graph_stats = await self.mindgraph.get_graph_stats()
        density_snapshot = await self.density.snapshot()
        readiness = await self.density.check_promotion_readiness()
        queue_stats = await self.approval_queue.stats()
        return {
            "grid": "online" if self._ready else "offline",
            **cluster_metadata(),
            "soul": self.soul.declare(),
            "mindgraph": graph_stats,
            "dcx": {
                "connected": self.dcx.connected,
                "models": {l.value: self.dcx._models[l] for l in DCXLayer},
            },
            "provenance": {
                "total_cycles": self.provenance.total_cycles,
                "recent": self.provenance.recent(3),
            },
            "moscripts": self.moscript.list_scripts(),
            "density": {
                **density_snapshot.to_dict(),
                "promotion_ready": readiness["ready"],
                "promotion_gaps": readiness["gaps"],
            },
            "queue": queue_stats,
            "seal": SEAL_GLYPH,
        }
