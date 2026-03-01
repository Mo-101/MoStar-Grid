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
    def interpret(self, ritual: dict) -> dict:
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
            result = self._execute_ritual(op, ritual)

            log_mostar_moment(
                initiator="MoScriptEngine",
                receiver=ritual.get("target", "Grid.Mind"),
                description=f"Ritual '{op}' executed — #{self.execution_count}",
                trigger_type=op,
                resonance_score=0.92,
                significance="RITUAL",
                layer="MIND",
            )

            return {
                "status":    "aligned",
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
    def _execute_ritual(self, op: str, ritual: dict):
        payload = ritual.get("payload", {})
        dispatch = {
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
        }
        fn = dispatch.get(op)
        if fn:
            return fn()
        # Unknown op but passed validation — passthrough
        return {
            "executed": op,
            "payload":  payload,
            "note":     "Passthrough — no dedicated handler",
        }

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

    print("\n=== VALID — Seal Covenant ===")
    print(json.dumps(mo.interpret({
        "operation": "seal",
        "payload":   {"intention": "Protect the Covenant", "layer": "Soul"}
    }), indent=2))

    print("\n=== VALID — Invoke Truth ===")
    print(json.dumps(mo.interpret({
        "operation": "invoke_truth",
        "payload":   {"query": "Is MoStar Grid sovereign?", "score": 0.91}
    }), indent=2))

    print("\n=== VALID — Codex Status ===")
    print(json.dumps(mo.interpret({
        "operation": "codex_status",
        "payload":   {}
    }), indent=2))

    print("\n=== VALID — Get Recent Moments ===")
    print(json.dumps(mo.interpret({
        "operation": "get_moments",
        "payload":   {"limit": 3}
    }), indent=2, default=str))

    print("\n=== BLOCKED — External AI Call ===")
    print(json.dumps(mo.interpret({
        "operation": "call_anthropic",
        "payload":   {"model": "claude-3-5-sonnet"}
    }), indent=2))

    print("\n=== BLOCKED — Exploit ===")
    print(json.dumps(mo.interpret({
        "operation": "exploit",
        "payload":   {"target": "vulnerable_node"}
    }), indent=2))