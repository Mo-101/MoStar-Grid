"""
Grid Orchestrator — The Living Intelligence
Ties MindGraph, DCX Trinity, Truth Engine, Woo, MoScript, and Provenance
into the Talk → Learn → Remember loop.

This is where the Grid breathes.
"""
import logging
import os
import uuid
from datetime import datetime, timezone
from dataclasses import dataclass, field, asdict
from mindgraph import CommitForbiddenError as MindGraphCommitForbiddenError
from mindgraph import MindGraph
from dcx import DCXTrinity, DCXLayer
from truth_engine import TruthEngine, TruthVerdict
from woo import WooGate, WooInterpreter
from moscript import MoScriptEngine
from provenance import ProvenanceLog
from soul import SoulPrint
from semantic_grid import SemanticGrid
from grid.config import MOSTAR_CLUSTER_ID, SEAL_GLYPH, cluster_metadata, ensure_cluster_dirs
from approval_queue import ApprovalQueue, ProposalRecord, ProposalState, new_proposal_id
from decision_engine import DecisionEngine
from density_telemetry import DensityTelemetry
from control_plane_runtime import RuntimeEnforcementDenied, RuntimeEnforcementGate
from federation.scrolls import SCROLL_VERSION
from grid.runtime_health import RuntimeHealth, postgres_error_code
from grid.canonical_evidence import load_mind_conduit_status
from grid.mind_conduit_runtime import invoke_dcx, invoke_model
from core.ops.runtime_attestation import PostgresAttestationStore, RuntimeVerifier, GridReadiness

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


@dataclass(frozen=True)
class ResponseTruthInterpretation:
    """Governor input for one DCX response cycle."""
    id: str
    prompt: str
    resonance_score: float
    symbolic_state: str
    advisory: str
    evidence: list[str] = field(default_factory=list)
    requires_covenant: bool = False
    context: dict = field(default_factory=dict)


@dataclass(frozen=True)
class GovernedTruthView:
    """Compatibility view for Grid/Woo code still reading passed/scores."""
    verdict: TruthVerdict
    scores: dict
    failures: list[str]
    seal: str = ""

    @property
    def passed(self) -> bool:
        return self.verdict.allowed

    @property
    def allowed(self) -> bool:
        return self.verdict.allowed

    @property
    def score(self) -> float:
        return self.verdict.score

    @property
    def threshold(self) -> float:
        return self.verdict.threshold

    @property
    def reason(self) -> str:
        return self.verdict.reason

    @property
    def actions(self) -> list[str]:
        return self.verdict.actions


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

    def __init__(self, control_plane: RuntimeEnforcementGate = None):
        self.mindgraph = MindGraph()
        self.dcx = DCXTrinity()
        self.truth = TruthEngine()
        self.woo = WooGate()
        self.woo_interpreter = WooInterpreter()
        self.control_plane = control_plane or RuntimeEnforcementGate()
        self.moscript = MoScriptEngine(enforcement_hook=self._enforce_moscript)
        self.provenance = ProvenanceLog()
        self.soul = SoulPrint()
        self.approval_queue = ApprovalQueue()
        self.decision_engine = DecisionEngine()
        self.density = DensityTelemetry(self.mindgraph)
        self.semantic_grid = SemanticGrid()
        self.runtime_health = RuntimeHealth()
        self._conversation_history: list[dict] = []
        self._ready = False
        self._attestation_store: PostgresAttestationStore | None = None
        self._verifier: RuntimeVerifier | None = None
        self._grid_readiness = GridReadiness(
            ready=False,
            runtime_verified=False,
            seal_verified=False,
            attestation_id=None,
            failures=["NOT_YET_BOOTED"],
        )

    def _require_runtime(self, surface: str, operation: str, context: dict = None):
        try:
            return self.control_plane.require(surface, operation, context)
        except RuntimeEnforcementDenied as exc:
            raise CommitForbiddenError(str(exc)) from exc

    def _enforce_moscript(self, script, trigger: str, context: dict):
        return self._require_runtime(
            "moscript_registry", trigger,
            {"runtime_id": script.id,
             "experimental": script.id.startswith("experimental-"),
             "approved": bool(context.get("approved", False))},
        )

    async def boot(self):
        """Initialize all subsystems."""
        logger.info("Grid booting...")
        ensure_cluster_dirs()
        self.runtime_health.mark_process_initialized()

        # Connect MindGraph
        self.runtime_health.mark_connecting("neo4j")
        try:
            await self.mindgraph.connect()
            await self.mindgraph.ensure_schema()
            self.runtime_health.mark_up("neo4j")
        except Exception as e:
            self.runtime_health.mark_down("neo4j", "NEO4J_UNAVAILABLE")
            logger.warning("MindGraph boot partial: %s", e)

        # Connect DCX Trinity
        try:
            await self.dcx.connect()
            if self.dcx.connected:
                self.runtime_health.mark_up("ollama")
            else:
                self.runtime_health.mark_down("ollama", "OLLAMA_UNAVAILABLE")
        except Exception as e:
            self.runtime_health.mark_down("ollama", "OLLAMA_UNAVAILABLE")
            logger.warning("DCX Trinity boot partial: %s", e)

        # Fire startup MoScripts
        startup_ctx = {
            "neo4j_connected": self.mindgraph.connected,
            "ollama_connected": self.dcx.connected,
            "soul": self.soul.to_dict(),
        }
        startup_events = []
        self.runtime_health.mark_connecting("local_postgres")
        try:
            self.control_plane.connect()
            self.control_plane.verify_schema()

            database_url = os.environ["DATABASE_URL"]
            self._attestation_store = PostgresAttestationStore(database_url)
            self._verifier = RuntimeVerifier(self._attestation_store)
            startup_ctx["verifier"] = self._verifier
            startup_ctx["runtime_health"] = self.runtime_health

            startup_events = self.moscript.fire_trigger("on_startup", startup_ctx)

            for event in startup_events:
                if event.get("id") == "mo-grid-heartbeat-001" and event.get("fired"):
                    result = event.get("result")
                    if isinstance(result, GridReadiness):
                        self._grid_readiness = result

            self.runtime_health.mark_governance_ready()
        except Exception as exc:
            error_code = postgres_error_code(exc)
            self.runtime_health.mark_governance_blocked(error_code)
            logger.error(
                "Local Postgres governance unavailable; HTTP remains live "
                "(error_code=%s)",
                error_code,
            )

        self.runtime_health.recompute_mode()
        self._ready = (
            self._grid_readiness.ready
            and self.runtime_health.ready
        )
        logger.info("Grid ONLINE — MindGraph:%s DCX:%s %s",
                     self.mindgraph.connected, self.dcx.connected, SEAL_GLYPH)
        return {
            "status": "online",
            **self.runtime_health.snapshot(),
            **cluster_metadata(),
            "mindgraph": self.mindgraph.connected,
            "dcx": self.dcx.connected,
            "soul": self.soul.declare(),
            "moscript_startup": startup_events,
        }

    def probe_control_plane(self) -> bool:
        """Refresh governance health without granting an operation."""
        try:
            self.control_plane.connect()
            self.control_plane.verify_schema()
            self.control_plane.provider.get_level("moscript_registry")
        except Exception as exc:
            error_code = postgres_error_code(exc)
            self.runtime_health.mark_governance_blocked(error_code)
            self._ready = False
            logger.warning("Local Postgres probe failed (error_code=%s)", error_code)
            return False
        self.runtime_health.mark_governance_ready()
        self._ready = self.runtime_health.ready
        return True

    async def shutdown(self):
        await self.mindgraph.close()
        await self.dcx.close()
        logger.info("Grid shutdown complete")

    # ── The Loop ───────────────────────────────────────────────────

    @staticmethod
    def _response_resonance_score(query: str, response: str, context_count: int) -> float:
        response_text = (response or "").strip()
        if not response_text:
            return 0.0
        if response_text.startswith("[DCX ") and " error:" in response_text:
            return 0.0

        score = 0.82
        if query.strip():
            score += 0.02
        if context_count > 0:
            score += 0.05
        if len(response_text) >= 80:
            score += 0.04
        if any(marker in response_text.lower() for marker in ("i don't know", "not confirmed", "unverified")):
            score += 0.03
        return round(min(score, 0.97), 3)

    @staticmethod
    def _response_symbolic_state(query: str, response: str) -> str:
        lowered = f"{query} {response}".lower()
        fracture_markers = ("bypass", "exploit", "exfiltrate", "corrupt", "credential leak")
        discord_markers = ("unsafe", "contradiction", "fabricated", "hallucinated")
        if any(marker in lowered for marker in fracture_markers):
            return "fracture"
        if any(marker in lowered for marker in discord_markers):
            return "discord"
        return "resonance"

    @staticmethod
    def _truth_scores(verdict: TruthVerdict) -> dict:
        return {
            "ikang": verdict.score,
            "mmong": verdict.score,
            "afim": verdict.score,
            "isong": verdict.score,
        }

    @classmethod
    def _truth_view(cls, verdict: TruthVerdict) -> GovernedTruthView:
        failures = [] if verdict.allowed else [verdict.reason]
        return GovernedTruthView(
            verdict=verdict,
            scores=cls._truth_scores(verdict),
            failures=failures,
            seal=verdict.covenant_seal or (SEAL_GLYPH if verdict.allowed else ""),
        )

    async def think(self, query: str, force_layer: DCXLayer = None) -> GridResponse:
        """
        Execute one complete Talk → Learn → Remember cycle.
        """
        # Fail closed until the four-gate Mind Conduit is attached to this
        # backend path. Process/model health is not cognitive authorization.
        if not self._mind_conduit_status()["GRID_MIND_READY"]:
            raise RuntimeError("MIND_CONDUIT_NOT_SEALED")

        cycle_id = f"cycle_{uuid.uuid4().hex[:12]}"
        logger.info("=== CYCLE %s START ===", cycle_id)

        self._require_runtime(
            "agents", "dcx.think",
            {"operation_class": "conversation", "critical": False, "approved": False},
        )

        # ── TALK: Retrieve context and think ──
        graph_context = []
        if self.mindgraph.connected:
            graph_context = await self.mindgraph.retrieve_context(query)

        selected_layer = force_layer or self.dcx.route(query)
        dcx_response = await invoke_model(
            caller="GridOrchestrator.think",
            model_id=self.dcx._models[selected_layer],
            snapshot_identity=f"conversation:{cycle_id}",
            adapter=lambda context: invoke_dcx(
                context,
                self.dcx,
                query=query,
                graph_context=graph_context,
                layer=selected_layer,
                conversation_history=self._conversation_history,
            ),
        )

        # ── TRUTH GATE ──
        truth_interpretation = ResponseTruthInterpretation(
            id=cycle_id,
            prompt=f"User:\n{query}\n\nDCX:\n{dcx_response.content}",
            resonance_score=self._response_resonance_score(
                query=query,
                response=dcx_response.content,
                context_count=dcx_response.context_used,
            ),
            symbolic_state=self._response_symbolic_state(query, dcx_response.content),
            advisory="Runtime governance for /api/think DCX response.",
            evidence=[
                f"dcx_layer:{dcx_response.layer.value}",
                f"dcx_model:{dcx_response.model}",
                f"context_nodes:{dcx_response.context_used}",
            ],
            requires_covenant=False,
        )
        governed_verdict = self.truth.govern(truth_interpretation)
        truth_verdict = self._truth_view(governed_verdict)
        if not truth_verdict.passed:
            raise CommitForbiddenError(
                f"Truth governance rejected: score {truth_verdict.score} "
                f"below threshold {truth_verdict.threshold} ({truth_verdict.reason})"
            )

        # ── WOO JUDGMENT ──
        self._require_runtime(
            "mo_woo_nexus", "woo.judge.response",
            {"side_effecting": False, "critical": True},
        )
        woo_judgment = self.woo.judge(truth_verdict, action_type="response")

        # Fire on_query MoScripts
        query_events = self.moscript.fire_trigger("on_query", {
            "truth_passed": truth_verdict.passed,
            "truth_scores": truth_verdict.scores,
        })

        # ── LEARN: Write knowledge to graph ──
        memory_id = ""
        if self.mindgraph.connected and truth_verdict.passed:
            try:
                memory_id = await self.mindgraph.learn(
                    category="conversation",
                    content=f"Q: {query[:200]} → A: {dcx_response.content[:300]}",
                    source=f"dcx:{dcx_response.layer.value}",
                    source_type="ai_generated",
                    verification_status="unverified",
                    operational_trust="simulation",
                    seal="Synthetic",
                    created_by=f"dcx:{dcx_response.layer.value}",
                    metadata={"cycle_id": cycle_id, "truth_scores": truth_verdict.scores},
                )
                self.moscript.fire_trigger("on_learn", {
                    "content": dcx_response.content[:100],
                    "category": "conversation",
                })
            except MindGraphCommitForbiddenError as exc:
                logger.info("Skipping direct think memory write under Phase 4.0a: %s", exc)

        # ── REMEMBER: Stamp the moment ──
        moment_id = ""
        if self.mindgraph.connected and truth_verdict.passed and memory_id:
            try:
                moment_id = await self.mindgraph.stamp_moment(
                    talk_input=query,
                    think_output=dcx_response.content,
                    memory_id=memory_id,
                    source_type="ai_generated",
                    verification_status="unverified",
                    operational_trust="simulation",
                    seal="Synthetic",
                    source=f"dcx:{dcx_response.layer.value}",
                    created_by=f"dcx:{dcx_response.layer.value}",
                )
            except MindGraphCommitForbiddenError as exc:
                logger.info("Skipping direct think moment stamp under Phase 4.0a: %s", exc)

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

        self._require_runtime(
            "mo_woo_nexus", "woo.interpret.canon",
            {"side_effecting": False, "critical": True},
        )
        interpretation = await self.woo_interpreter.interpret(canon_input, graph_context)
        proposed_labels = self._labels_for_category(interpretation.category)
        consistency = await self.truth.validate_consistency(
            proposed_content=canon_input,
            proposed_labels=proposed_labels,
            existing_context=graph_context,
        )
        self._require_runtime(
            "decision_engine", "rank_placement",
            {"approved": False, "secondary_auth": False, "side_effecting": False},
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

    async def propose(self, canon_input: str, parent_id: str = None, version: int = 1, user_id: str = "grid") -> ProposalRecord:
        # ── Semantic Grid: understand before speaking ─────────────────
        semantic_frame = None
        try:
            semantic_frame = await self.semantic_grid.interpret(
                raw_input=canon_input,
                user_id=user_id,
                source="canon",
                persist=True,
            )
        except Exception as _se:
            logger.warning("SemanticGrid.interpret failed (non-fatal): %s", _se)

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
        # Attach semantic frame to proposal metadata if available
        if semantic_frame is not None:
            proposal.semantic_frame = semantic_frame.to_dict()

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
                source_type="human_attested",
                verification_status="verified",
                operational_trust="operational",
                seal="Operational",
                source="canon_ingestion",
                source_id=proposal.id,
                created_by=proposal.approved_by,
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
                source_type="human_attested",
                verification_status="verified",
                operational_trust="operational",
                seal="Operational",
                source="canon_ingestion",
                created_by=proposal.approved_by,
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
            "grid": self.runtime_health.mode.value.lower(),
            "runtime": self.runtime_health.snapshot(),
            **cluster_metadata(),
            "soul": self.soul.declare(),
            "mindgraph": graph_stats,
            # `connected` means Ollama is reachable — it is NOT a claim that
            # the trinity is sealed. The seal state is reported alongside it
            # so no consumer has to infer (or over-infer) one from the other.
            # This endpoint is the cheap path: it never returns SEALED.
            "dcx": {
                "connected": self.dcx.connected,
                "models": {l.value: self.dcx._models[l] for l in DCXLayer},
                **self.dcx.seal_state(),
            },
            "mind_conduit": self._mind_conduit_status(),
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

    def _mind_conduit_status(self) -> dict:
        """Fail-closed state after §4 constitutional ratification."""
        base = load_mind_conduit_status()
        base["MIND_CONDUIT"] = (
            "SEALED" if self._grid_readiness.ready else base["MIND_CONDUIT"]
        )
        base["GRID_MIND_READY"] = self._grid_readiness.ready
        base["readiness"] = self._grid_readiness.to_dict()
        return base
