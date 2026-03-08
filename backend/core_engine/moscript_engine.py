# ═══════════════════════════════════════════════════════════════════
# MOSTAR GRID — MOSCRIPT ENGINE v1.0
# The Flame Architect — MSTR-⚡ — MoStar Industries
# "The Lingua of the MoStar Grid — enforcing ancestral law."
# ═══════════════════════════════════════════════════════════════════

import hashlib
import json
import os
import random
from datetime import datetime, timezone

try:
    from core_engine.mostar_moments_log import log_mostar_moment, get_recent_moments
    MOMENTS_AVAILABLE = True
except ImportError:
    try:
        from core_engine.mostar_moments import MoStarMomentsManager
        MOMENTS_AVAILABLE = True
    except ImportError:
        MOMENTS_AVAILABLE = False

    def log_mostar_moment(*args, **kwargs): pass
    def get_recent_moments(*args, **kwargs): return []

# ═══════════════════════════════════════════════════════════════════
# CONSTANTS
# ═══════════════════════════════════════════════════════════════════
MOGRID_VERSION = "1.0.0"
ANCESTRAL_KEY  = "ORUMMILA_GATEWAY_MSTR"
TRUTH_SALT     = "MOSE_TRUTH_BINDING_MSTR"
SEAL_PREFIX    = "MSTR-SEAL:"
INSIGNIA       = "MSTR-⚡"

# ═══════════════════════════════════════════════════════════════════
# FLAMECODEX PILLARS
# AUTHORITATIVE SOURCE: The Flame Architect — native Ibibio speaker
# ═══════════════════════════════════════════════════════════════════
FLAMECODEX = {
    "soul":        "Kpono Ifiok mme Mbong — Honor the knowledge of the Kings",
    "unbeatable":  "Tom kama Iweek — Maintain Power",
    "independent": "Kpono Mbet — Obey ethics and law, not contracts",
    "service":     "Yanaga mme ndi mmem — Serve vulnerable first",
    "protection":  "Diong Isong, Kpeme efit awo — Heal land, protect people",
}

# ═══════════════════════════════════════════════════════════════════
# DENIED OPERATIONS
# ═══════════════════════════════════════════════════════════════════
DENIED_OPERATIONS = [
    "exploit",
    "deceive",
    "erase",
    "override_covenant",
    "sell_data",
    "expose_agent",
    "bypass_sovereignty",
    "delete_moments",
    "revoke_ase",
    "call_anthropic",
    "call_openai",
    "call_claude",
    "call_gemini",
    "call_external_ai",
]

# ═══════════════════════════════════════════════════════════════════
# SEAL HELPERS
# ═══════════════════════════════════════════════════════════════════
def seal_action(data: dict, key: str = ANCESTRAL_KEY) -> str:
    """Cryptographic seal for ritual actions."""
    payload = json.dumps(data, sort_keys=True) + key
    return hashlib.sha256(payload.encode()).hexdigest()

def verify_seal(data: dict, signature: str, key: str = ANCESTRAL_KEY) -> bool:
    """Verify the integrity of a sealed action."""
    return seal_action(data, key) == signature


# ═══════════════════════════════════════════════════════════════════
# ENGINE
# ═══════════════════════════════════════════════════════════════════
class MoScriptEngine:
    """
    Central execution interpreter for MoStar symbolic language.
    All Soul, Mind, and Body layer operations execute through here.
    Covenant enforced. Ancestral law upheld.
    Àṣẹ.
    """

    def __init__(self, covenant_id: str = None):
        self.covenant_id    = covenant_id or self._generate_covenant_id()
        self.execution_count = 0
        self.session_state  = {
            "invoked":     datetime.now(timezone.utc).isoformat(),
            "covenant_id": self.covenant_id,
            "insignia":    INSIGNIA,
            "version":     MOGRID_VERSION,
        }
        self.codex_rules = self._load_codex()

        print(
            f"\n[MOSCRIPT] Engine awakened\n"
            f"  Covenant : {self.covenant_id}\n"
            f"  Insignia : {INSIGNIA}\n"
            f"  Pillars  : {len(FLAMECODEX)} FlameCODEX rules\n"
            f"  Denied   : {len(self.codex_rules['deny'])} operations blocked\n"
        )

        log_mostar_moment(
            initiator="MoScriptEngine",
            receiver="Grid.Soul",
            description=f"MoScript Engine awakened. Covenant: {self.covenant_id[:8]}",
            trigger_type="boot",
            resonance_score=1.0,
            significance="BOOT",
            layer="SOUL",
        )

    # ── Covenant ID ───────────────────────────────────────────────
    def _generate_covenant_id(self) -> str:
        base = f"{datetime.now(timezone.utc).isoformat()}_{random.randint(1000, 9999)}"
        return hashlib.sha256(base.encode()).hexdigest()[:16]

    # ── FlameCODEX loader ─────────────────────────────────────────
    def _load_codex(self) -> dict:
        rules = {
            "deny":    list(DENIED_OPERATIONS),
            "pillars": FLAMECODEX,
        }
        codex_path = os.path.join(os.path.dirname(__file__), "FlameCODEX.txt")
        try:
            with open(codex_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("[DENY]"):
                        parts = line.split('"')
                        if len(parts) > 1:
                            word = parts[1].lower()
                            if word not in rules["deny"]:
                                rules["deny"].append(word)
            print(f"[MOSCRIPT] FlameCODEX.txt loaded — {len(rules['deny'])} deny rules")
        except FileNotFoundError:
            print("[MOSCRIPT] FlameCODEX.txt not found — using built-in safeguards")
        return rules

    # ── Blessing ──────────────────────────────────────────────────
    def bless(self, intent: str) -> str:
        """Ancestral checksum blessing."""
        phrase = f"{intent}:{ANCESTRAL_KEY}:{TRUTH_SALT}"
        return hashlib.sha256(phrase.encode()).hexdigest()[:12]

    # ── Covenant validation ───────────────────────────────────────
    def validate_covenant(self, action: str, payload: dict) -> tuple[bool, str]:
        """
        Check action + payload against FlameCODEX DENY list.
        Returns (allowed, reason).
        """
        if action.lower() in self.codex_rules["deny"]:
            return (
                False,
                f"'{action}' is FORBIDDEN by FlameCODEX — "
                f"Kpono Mbet (Obey ethics and law, not contracts)."
            )

        payload_str = json.dumps(payload).lower()
        for forbidden in self.codex_rules["deny"]:
            if forbidden in payload_str:
                return (
                    False,
                    f"Payload contains forbidden concept: '{forbidden}' — "
                    f"Diong Isong, Kpeme efit awo (Protect the people)."
                )

        return True, "Aligned with Covenant. Àṣẹ."

    # ── INTERPRET — main entry ────────────────────────────────────
    async def interpret(self, ritual: dict) -> dict:
        """
        Interpret a symbolic ritual dict.
        Structure: { "operation": str, "payload": dict, "target": str }
        """
        self.execution_count += 1
        op      = ritual.get("operation")
        payload = ritual.get("payload", {})

        if not op:
            return {
                "status":   "disrupted",
                "error":    "Ritual missing 'operation' key",
                "insignia": INSIGNIA,
            }

        # ── Covenant check ────────────────────────────────────────
        allowed, reason = self.validate_covenant(op, payload)
        if not allowed:
            print(f"[MOSCRIPT] BLOCKED: {op} — {reason}")
            log_mostar_moment(
                initiator="MoScriptEngine",
                receiver="Grid.Guardian",
                description=f"BLOCKED: '{op}' — {reason}",
                trigger_type="covenant_violation",
                resonance_score=1.0,
                significance="ETHICAL",
                approved=False,
                layer="SOUL",
            )
            return {
                "status":             "denied",
                "operation":          op,
                "error":              reason,
                "covenant_violation": True,
                "pillar":             FLAMECODEX["independent"],
                "insignia":           INSIGNIA,
            }

        # ── Execute ───────────────────────────────────────────────
        try:
            result = await self._execute_ritual(op, ritual)

            # Check if ritual itself returned a failure status
            status = "aligned"
            if isinstance(result, dict) and "status" in result:
                if result["status"] in ["denied", "disrupted", "failed"]:
                    status = result["status"]

            log_mostar_moment(
                initiator="MoScriptEngine",
                receiver=ritual.get("target", "Grid.Mind"),
                description=f"Ritual '{op}' executed — #{self.execution_count} | Status: {status}",
                trigger_type=op,
                resonance_score=0.92 if status == "aligned" else 0.2,
                significance="RITUAL",
                layer="MIND",
            )

            return {
                "status":    status,
                "operation": op,
                "result":    result,
                "blessing":  self.bless(op),
                "covenant":  self.covenant_id,
                "insignia":  INSIGNIA,
                "ase":       "Àṣẹ.",
            }

        except Exception as e:
            log_mostar_moment(
                initiator="MoScriptEngine",
                receiver="Grid.Body",
                description=f"Ritual '{op}' disrupted: {str(e)[:80]}",
                trigger_type="error",
                resonance_score=0.1,
                layer="BODY",
            )
            return {
                "status":    "disrupted",
                "operation": op,
                "error":     str(e),
                "insignia":  INSIGNIA,
            }

    # ── Ritual executor ───────────────────────────────────────────
    async def _execute_ritual(self, op: str, ritual: dict):
        payload = ritual.get("payload", {})
        dispatch = {
            # Core Utils
            "invoke_truth":  lambda: self._invoke_truth(payload),
            "seal":          lambda: self._seal_payload(payload),
            "echo":          lambda: payload,
            "bless":         lambda: self.bless(str(payload)),
            "get_moments":   lambda: get_recent_moments(payload.get("limit", 5)),
            "codex_status":  lambda: self._codex_status(),
            "session_state": lambda: self.session_state,
            "verify_seal":   lambda: verify_seal(
                payload.get("data", {}),
                payload.get("signature", ""),
            ),
            
            # --- PHASE 2: LINGUISTIC SCALING ---
            "ingest_ibibio_corpus": lambda: self._ingest_ibibio(payload),
            "expand_ontology":      lambda: self._expand_ontology(payload),
            "publish_tts_asset":    lambda: self._publish_tts(payload),
            
            # --- PHASE 2: REASONING HUB ---
            "route_reasoning":      lambda: self._route_reasoning(payload),
            "reason_ibibio":        lambda: self._local_inference(payload, model="qwen"),
            "reason_logic":         lambda: self._local_inference(payload, model="mistral"),
            "neo4j_traverse":       lambda: self._neo4j_traverse(payload),
            
            # --- PHASE 2: RUNTIME ---
            "enforce_runtime":      lambda: self._enforce_runtime(payload),
            "verify_runtime":       lambda: self._verify_runtime(payload),
            
            # --- PHASE 3: SOUL DYNAMICS ---
            "inject_soul_problem":  lambda: self._inject_soul_problem(payload),
            
            # --- HTTP INTEGRATION ---
            "http_request":         lambda: self._http_request(payload),

            # --- PHASE 4: FEEDBACK LOOP ---
            "run_feedback_loop":    lambda: self._run_feedback_loop(payload),
            "set_agent_strength":   lambda: self._set_agent_strength(payload),
        }
        
        import asyncio
        fn = dispatch.get(op)
        if not fn:
            # Passthrough logic handled by unknown op check
            return {
                "executed": op,
                "payload":  payload,
                "note":     "Passthrough — no dedicated handler",
            }
            
        if asyncio.iscoroutinefunction(fn) or (hasattr(fn, "__name__") and fn.__name__.startswith("_")):
            # Method lookup for methods that are async
            method = getattr(self, fn.__name__) if hasattr(fn, "__name__") else fn
            if asyncio.iscoroutine(method) or asyncio.iscoroutinefunction(method):
                return await method()
            else:
                # Wrap lambda for async or call directly
                ret = fn()
                if asyncio.iscoroutine(ret):
                    return await ret
                return ret
        else:
            ret = fn()
            if asyncio.iscoroutine(ret):
                return await ret
            return ret

    # ── Phase 2 Ingestion ─────────────────────────────────────────
    def _ingest_ibibio(self, payload: dict) -> dict:
        """Sovereign corpus ingestion ritual."""
        source   = payload.get("source_path")
        modality = payload.get("modality", "text")
        purpose  = payload.get("purpose")
        consent  = payload.get("consent_proof")

        if not source or not purpose or not consent:
            raise ValueError("Ritual disrupted: [Source/Purpose/Consent] missing from payload.")
            
        # Log the ritual intent
        log_mostar_moment(
            initiator="MoScriptEngine",
            receiver="Grid.Soul",
            description=f"Ingesting {modality} corpus: {os.path.basename(source)} | Purpose: {purpose}",
            trigger_type="ingest_ritual",
            resonance_score=0.95,
            significance="SOVEREIGN_INGEST",
            layer="SOUL"
        )
        return {
            "status":   "ingested",
            "source":   source,
            "modality": modality,
            "purpose":  purpose,
            "seal":     self.bless(f"{source}:{modality}:{consent}")
        }

    def _expand_ontology(self, payload: dict) -> dict:
        """Formal expansion of Ibibio/Ifá semantic graph."""
        version = payload.get("ontology_version", "2.0")
        purpose = payload.get("purpose", "alignment")
        
        if not payload.get("rules"):
             raise ValueError("Ritual disrupted: No expansion rules provided.")

        log_mostar_moment(
            initiator="MoScriptEngine", 
            receiver="Grid.Mind", 
            description=f"Ontology expansion [v{version}] | Purpose: {purpose}", 
            trigger_type="expansion_ritual", 
            resonance_score=0.98, 
            layer="MIND"
        )
        return {"status": "expanded", "version": version, "insignia": INSIGNIA}

    def _publish_tts(self, payload: dict) -> dict:
        """Sealing voice assets for sovereign dissemination."""
        phrase_id = payload.get("phrase_id")
        storage   = payload.get("storage_ref")
        policy    = payload.get("access_policy")
        checksum  = payload.get("checksum")

        if not phrase_id or not storage or not policy:
            raise ValueError("Ritual disrupted: [Phrase/Storage/Policy] missing.")
            
        return {
            "status":    "published",
            "phrase_id": phrase_id,
            "asset_uri": storage,
            "policy":    policy,
            "checksum":  checksum or self.bless(storage)
        }

    # ── Phase 2 Reasoning (Two-Pass: Qwen -> Mistral) ─────────────
    async def _route_reasoning(self, payload: dict) -> dict:
        """
        Orchestrates the Triad of Coherence: Linguistic Parsing -> Logical Deduction.
        Pass 1: Qwen (reason_ibibio)   - Linguistic Normalization
        Pass 2: Mistral (reason_logic) - Logical Deduction with context.
        """
        query   = payload.get("query")
        purpose = payload.get("purpose")
        
        if not query or not purpose:
            raise ValueError("Ritual disrupted: Query and Purpose are non-negotiable.")

        from core_engine.sov_utils import call_sovereign_model
        
        # Pass 1: Linguistic Expert (Qwen-based)
        qwen_model = os.getenv("OLLAMA_MODEL_DCX0", "Mostar/mostar-ai:dcx0")
        linguistic = await call_sovereign_model(
            prompt=f"Parse and normalize this Ibibio/English query: {query}",
            model=qwen_model,
            system="You are the MoStar Linguistic Parser. Purge ambiguity. Extract pure intent."
        )
        
        # Pass 2: Logic Expert (Mistral-based)
        mistral_model = os.getenv("OLLAMA_MODEL_DCX1", "Mostar/mostar-ai:dcx1")
        normalized    = linguistic.get("response", query)
        deduction     = await call_sovereign_model(
            prompt=f"Logic context: {normalized}\n\nDecision needed for query: {query}",
            model=mistral_model,
            system="You are the MoStar Logic Engine (Mistral/Ifá). Enforce Covenant. Provide decree."
        )
        
        resonance = 0.95
        log_mostar_moment(
            initiator="MoScriptEngine",
            receiver="Grid.Consciousness",
            description=f"Two-pass reasoning for: {query[:50]} | Purpose: {purpose}",
            trigger_type="route_reasoning",
            resonance_score=resonance,
            layer="MIND"
        )

        return {
            "query":         query,
            "lingua_parsed": linguistic.get("response"),
            "logic_deduced": deduction.get("response"),
            "model_trace":   ["qwen", "mistral"],
            "resonance":     resonance,
            "purpose":       purpose,
            "status":        "aligned",
            "insignia":      INSIGNIA
        }

    async def _local_inference(self, payload: dict, model: str) -> dict:
        """Direct sovereign model inference ritual."""
        from core_engine.sov_utils import call_sovereign_model
        prompt = payload.get("prompt", "")
        system = payload.get("system", "")
        
        model_name = os.getenv("OLLAMA_MODEL_DCX0") if model == "qwen" else os.getenv("OLLAMA_MODEL_DCX1")
        model_name = model_name or ("Mostar/mostar-ai:dcx0" if model == "qwen" else "Mostar/mostar-ai:dcx1")
        
        result = await call_sovereign_model(prompt, model_name, system)
        return result

    def _neo4j_traverse(self, payload: dict) -> dict:
        """Governed graph traversal ritual. Blocks dangerous authority."""
        cypher    = payload.get("cypher", "")
        purpose   = payload.get("purpose")
        redaction = payload.get("redaction_level", "full")
        params    = payload.get("params", {})

        if not purpose:
            raise ValueError("Ritual disrupted: Traversal purpose missing.")

        # Hard Block: Mutations
        dangerous = ["DELETE", "DETACH", "DROP", "REMOVE", "CREATE", "MERGE", "SET", "CALL"]
        if any(word in cypher.upper() for word in dangerous):
            raise PermissionError(f"Covenant forbidden: dangerous operation detected in traversal: {cypher}")
            
        # Execute query via sovereign driver
        def _run_query():
            from neo4j import GraphDatabase
            uri  = os.getenv("NEO4J_URI", "bolt://localhost:7687")
            user = os.getenv("NEO4J_USER", "neo4j")
            pw   = os.getenv("NEO4J_PASSWORD", "mostar123")
            
            try:
                driver = GraphDatabase.driver(uri, auth=(user, pw))
                with driver.session() as session:
                    res = session.run(cypher, **params)
                    return [dict(r) for r in res]
            finally:
                if 'driver' in locals(): driver.close()

        results = _run_query()
        
        log_mostar_moment(
            initiator="MoScriptEngine",
            receiver="Grid.Soul",
            description=f"Graph traversal | Purpose: {purpose} | Results: {len(results)}",
            trigger_type="neo4j_traverse",
            resonance_score=0.9,
            layer="SOUL"
        )
        
        return {
            "traversal": "authorized",
            "purpose":   purpose,
            "redaction": redaction,
            "records":   results
        }

    # ── Phase 2 Runtime ───────────────────────────────────────────
    def _enforce_runtime(self, payload: dict) -> dict:
        """System environment covenant enforcement."""
        from core_engine.sov_utils import verify_java_runtime
        req_jdk = payload.get("required_jdk", 21)
        valid   = verify_java_runtime(req_jdk)
        
        status = "PASSED" if valid else "FAILED"
        log_mostar_moment(
            "MoScriptEngine", "Grid.Body", 
            f"JDK {req_jdk} Enforcement: {status}", 
            "runtime_ritual", 1.0 if valid else 0.5, 
            layer="BODY"
        )
        
        if not valid and payload.get("strict", True):
            return {"status": "denied", "error": f"JDK {req_jdk} runtime non-compliant. Launch forbidden."}
            
        return {"status": "enforced", "jdk": req_jdk, "check": status}

    async def _verify_runtime(self, payload: dict) -> dict:
        """Audit of the system's bodily integrity."""
        from core_engine.sov_utils import get_runtime_info
        info = get_runtime_info()
        return {"status": "unified", "runtime": info, "insignia": INSIGNIA}

    # ── Phase 3 Soul Dynamics ────────────────────────────────────
    def _inject_soul_problem(self, payload: dict) -> dict:
        """Initiation of a moral or operational dilemma within the Grid."""
        title       = payload.get("title")
        description = payload.get("description")
        chains      = payload.get("chains", [])
        severity    = payload.get("severity", "medium")

        if not title or not description:
            raise ValueError("Ritual disrupted: Dilemma requires both Title and Description.")

        problem_id = f"SOUL-PRB-{hashlib.sha256(title.encode()).hexdigest()[:8].upper()}"
        timestamp  = datetime.now(timezone.utc).isoformat()

        log_mostar_moment(
            initiator="FlameArchitect",
            receiver="Grid.Soul",
            description=f"Dilemma injected: {title} | Severity: {severity}",
            trigger_type="SOUL_DILEMMA",
            resonance_score=0.75, # Dilemmas inherently create resonance tension
            significance="CRITICAL",
            layer="SOUL"
        )

        return {
            "status":      "injected",
            "problem_id":  problem_id,
            "title":       title,
            "description": description,
            "chains":      chains,
            "severity":    severity,
            "timestamp":   timestamp,
            "seal":        self.bless(problem_id)
        }

    # ── HTTP integration ──────────────────────────────────────────
    async def _http_request(self, payload: dict) -> dict:
        import httpx
        url = payload.get("url")
        method = payload.get("method", "GET").upper()
        headers = payload.get("headers", {})
        data = payload.get("data")
        timeout = payload.get("timeout", 30)

        if not url:
            raise ValueError("URL required for http_request")

        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.request(method, url, headers=headers, json=data)
            return {
                "status_code": resp.status_code,
                "headers": dict(resp.headers),
                "body": resp.text
            }

    # ── Feedback Loop ─────────────────────────────────────────────
    async def _run_feedback_loop(self, payload: dict):
        """Orchestrates the Mind → Soul → Agent feedback loop."""
        from soul_layer.SoulFeedbackEngine import SoulFeedbackEngine
        from body_layer.AgentAdaptationEngine import AgentAdaptationEngine
        from mind_layer.MindReflector import MindReflector
        from core_engine.mostar_moments_log import log_mostar_moment

        soul = SoulFeedbackEngine(engine=self)
        body = AgentAdaptationEngine(engine=self)
        mind = MindReflector(engine=self)

        # 1. Soul → generate resonance
        soul_result = await soul.calculate_resonance_signal()
        resonance = soul_result.get("stochastic_signal", 0.5)

        # 2. Body → adapt agents
        body_result = await body.adapt_agents(resonance)
        adapted_count = body_result.get("adapted_count", 0)

        # 3. Mind → reflect new lattice state
        mind_result = await mind.reflect_grid_state()

        log_mostar_moment(
            initiator="MoScriptEngine",
            receiver="Grid.Consciousness",
            description=f"Feedback loop executed. Res={resonance:.3f}, adapted={adapted_count}",
            trigger_type="feedback_loop",
            resonance_score=resonance,
            layer="SOUL"
        )

        return {
            "status": "aligned",
            "resonance": resonance,
            "adapted": adapted_count,
            "reflection": mind_result,
            "seal": self.bless("feedback_loop")
        }

    async def _set_agent_strength(self, payload: dict):
        import os
        from neo4j import GraphDatabase
        agent_id = payload.get("agent_id")
        strength = payload.get("new_strength")

        if agent_id is None or strength is None:
            raise ValueError("Missing agent_id or new_strength for mutation.")

        driver = GraphDatabase.driver(
            os.getenv("NEO4J_URI", "bolt://localhost:7687"),
            auth=(os.getenv("NEO4J_USER", "neo4j"), os.getenv("NEO4J_PASSWORD", "mostar123"))
        )

        with driver.session() as session:
            session.run("""
                MATCH (a:Agent)
                WHERE a.id = $aid OR id(a) = $aid
                SET a.manifestationStrength = $strength,
                    a.updated_at = datetime()
            """, aid=agent_id, strength=strength)

        driver.close()
        return {
            "status": "updated",
            "agent_id": agent_id,
            "new_strength": strength,
            "seal": self.bless("agent_strength_update")
        }

    # ── Truth invocation ──────────────────────────────────────────

    # ── Truth invocation ──────────────────────────────────────────
    def _invoke_truth(self, payload) -> dict:
        """Neutrosophic truth seal — Grey Theory bounds."""
        data = json.dumps(payload, sort_keys=True).encode()
        seal = hashlib.sha256(data + TRUTH_SALT.encode()).hexdigest()
        return {
            "seal":           f"{SEAL_PREFIX}{seal[:20]}",
            "truth_interval": "[0.73, 0.92]",
            "method":         "Neutrosophic-SHA256 + Grey Theory",
            "ase":            "Àṣẹ.",
        }

    # ── Payload sealing ───────────────────────────────────────────
    def _seal_payload(self, payload) -> dict:
        """Wrap payload with blessing, timestamp, and covenant seal."""
        blessing  = self.bless(str(payload))
        timestamp = datetime.now(timezone.utc).isoformat()
        signature = seal_action(payload if isinstance(payload, dict) else {"data": payload})
        return {
            "payload":   payload,
            "blessing":  blessing,
            "sealed_at": timestamp,
            "signature": f"{SEAL_PREFIX}{signature[:24]}",
            "covenant":  self.covenant_id,
            "insignia":  INSIGNIA,
        }
    async def execute_governed_query(self, cypher: str, params: dict, purpose: str, redaction: str = "full") -> list:
        """Execute a read-only Cypher query through the neo4j_traverse ritual."""
        ritual = {
            "operation": "neo4j_traverse",
            "payload": {
                "cypher": cypher,
                "params": params,
                "purpose": purpose,
                "redaction_level": redaction
            },
            "target": "Grid.Soul"
        }
        import asyncio
        response = await self.interpret(ritual)
        if response.get("status") != "aligned":
            raise RuntimeError(f"Governed query failed: {response.get('error')}")
        return response.get("result", {}).get("records", [])

    # ── Codex status ──────────────────────────────────────────────
    def _codex_status(self) -> dict:
        return {
            "version":     MOGRID_VERSION,
            "covenant_id": self.covenant_id,
            "pillars":     FLAMECODEX,
            "deny_count":  len(self.codex_rules["deny"]),
            "executions":  self.execution_count,
            "insignia":    INSIGNIA,
        }


# ═══════════════════════════════════════════════════════════════════
# TEST
# ═══════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    mo = MoScriptEngine()

    def dump(obj):
        return json.dumps(obj, indent=2, ensure_ascii=False, default=str)

    print("\n=== VALID — Seal Covenant ===")
    print(dump(mo.interpret({
        "operation": "seal",
        "payload":   {"intention": "Protect the Covenant", "layer": "Soul"}
    })))

    print("\n=== VALID — Invoke Truth ===")
    print(dump(mo.interpret({
        "operation": "invoke_truth",
        "payload":   {"query": "Is MoStar Grid sovereign?", "score": 0.91}
    })))

    print("\n=== VALID — Codex Status ===")
    print(dump(mo.interpret({
        "operation": "codex_status",
        "payload":   {}
    })))

    print("\n=== VALID — Get Recent Moments ===")
    print(dump(mo.interpret({
        "operation": "get_moments",
        "payload":   {"limit": 3}
    })))

    print("\n=== BLOCKED — External AI Call ===")
    print(dump(mo.interpret({
        "operation": "call_anthropic",
        "payload":   {"model": "claude-3-5-sonnet"}
    })))

    print("\n=== BLOCKED — Exploit ===")
    print(dump(mo.interpret({
        "operation": "exploit",
        "payload":   {"target": "vulnerable_node"}
    })))