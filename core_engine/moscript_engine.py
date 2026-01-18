#!/usr/bin/env python3
"""
🔥 MoScript Engine v1.0 — The Lingua of the MoStar Grid
------------------------------------------------------
Acts as the unifying runtime for all Soul, Mind, and Body layers.
All modules execute through this interpreter — enforcing symbolic logic,
ancestral validation, and divine alignment.
"""

import hashlib, json, os, time, random
from datetime import datetime, timezone
try:
    from core_engine.mostar_moments import MoStarMomentsManager
    MOMENTS_AVAILABLE = True
except ImportError:
    MOMENTS_AVAILABLE = False

# === MoScript Constants ===
MOGRID_VERSION = "1.0.0"
ANCESTRAL_KEY = "Ọ̀RÚNMÌLÀ_GATEWAY"
TRUTH_SALT = "MÒṢE_TRUTH_BINDING"
SEAL_PREFIX = "qseal:"

def seal_action(data: dict, key: str) -> str:
    """Cryptographic seal for ritual actions."""
    payload = str(data) + key
    return hashlib.sha256(payload.encode()).hexdigest()

def verify_seal(data: dict, signature: str, key: str) -> bool:
    """Verify the integrity of a sealed action."""
    expected = seal_action(data, key)
    return expected == signature

class MoScriptEngine:
    """Central execution interpreter for MoStar symbolic language."""
    
    def __init__(self, covenant_id: str = None):
        """
        Initializes the MoScript Engine with a covenant ID.
        """
        self.covenant_id = covenant_id or self._generate_covenant_id()
        self.session_state = {"invoked": datetime.utcnow().isoformat()}
        self.codex_rules = self._load_codex()
        print(f"🕯️ MoScript Engine awakened under Covenant: {self.covenant_id}")

    def _load_codex(self) -> dict:
        """Loads the FlameCODEX rules for validation."""
        codex_path = os.path.join(os.path.dirname(__file__), "FlameCODEX.txt")
        rules = {"deny": [], "must": []}
        try:
            with open(codex_path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.startswith("[DENY]"):
                        # Extract keyword "Exploit" from [DENY] "Exploit": ...
                        parts = line.split('"')
                        if len(parts) > 1:
                            rules["deny"].append(parts[1].lower())
        except FileNotFoundError:
            print("⚠️ FlameCODEX not found. Operating with default safeguards.")
            rules["deny"] = ["exploit", "deceive", "erase"]
        return rules

    # ======= SOULPRINT =======
    def _generate_covenant_id(self) -> str:
        """Generates a covenant ID."""
        base = f"{datetime.utcnow().isoformat()}_{random.randint(1000,9999)}"
        return hashlib.sha256(base.encode()).hexdigest()[:16]

    def bless(self, intent: str):
        """Blesses a statement with ancestral checksum."""
        phrase = f"{intent}-{ANCESTRAL_KEY}-{TRUTH_SALT}"
        return hashlib.sha256(phrase.encode()).hexdigest()[:12]
        
    def validate_covenant(self, action: str, payload: dict) -> tuple[bool, str]:
        """
        Validates if an action/payload complies with the FlameCODEX.
        Returns: (is_allowed, reason)
        """
        # 1. Check Action against DENY list
        if action.lower() in self.codex_rules["deny"]:
            return False, f"Action '{action}' is explicitly FORBIDDEN by FlameCODEX."

        # 2. Check Payload content against DENY list (simple keyword scan)
        payload_str = json.dumps(payload).lower()
        for forbidden in self.codex_rules["deny"]:
             if forbidden in payload_str:
                 return False, f"Payload contains forbidden concept: '{forbidden}'"

        return True, "Aligned with Covenant."

    # ======= MINDFLOW =======
    def interpret(self, ritual: dict) -> dict:
        """Interprets symbolic ritual instructions into executable logic."""
        try:
            op = ritual.get("operation")
            if not op:
                raise ValueError("Ritual lacks operation key.")
                
            # --- COVENANT CHECK ---
            allowed, reason = self.validate_covenant(op, ritual.get("payload", {}))
            if not allowed:
                print(f"🛑 COVENANT VIOLATION BLOCKED: {op} -> {reason}")
                if MOMENTS_AVAILABLE:
                   manager = MoStarMomentsManager()
                   manager.create_moment(
                       initiator="MoScript",
                       receiver="Grid.Mind", 
                       description=f"Blocked operation '{op}' violating FlameCODEX", 
                       trigger="ethical safeguard",
                       resonance_score=1.0, 
                       approved=False,
                       significance="ETHICAL"
                   )
                return {"status": "denied", "error": reason, "covenant_violation": True}
            # ----------------------

            result = self._execute_ritual(op, ritual)
            return {"status": "aligned", "operation": op, "result": result}
        except Exception as e:
            return {"status": "disrupted", "error": str(e)}

    # ======= BODYTASK =======
    def _execute_ritual(self, op: str, ritual: dict):
        """Executes operation according to ancestral law."""
        if op == "invoke_truth":
            return self._invoke_truth(ritual.get("payload"))
        elif op == "seal":
            return self._seal_payload(ritual.get("payload"))
        elif op == "echo":
            return ritual.get("payload", "Empty echo")
        else:
            # If not explicitly handled but passed validation, allow passing through
            # (Future: dynamic dispatch)
            return {"executed": op, "payload": ritual.get("payload")}

    # ======= TRUTH & SEAL =======
    def _invoke_truth(self, payload):
        """Verifies alignment through covenantal hashing."""
        data = json.dumps(payload, sort_keys=True).encode()
        seal = hashlib.sha256(data + TRUTH_SALT.encode()).hexdigest()
        return f"{SEAL_PREFIX}{seal[:20]}"

    def _seal_payload(self, payload):
        """Wraps payload with MoScript blessing and seal."""
        blessing = self.bless(str(payload))
        timestamp = datetime.now(timezone.utc).isoformat()

        return {
            "payload": payload,
            "blessing": blessing,
            "sealed_at": timestamp,
            "signature": f"{SEAL_PREFIX}{blessing}"
        }

# ======= ENTRYPOINT =======
if __name__ == "__main__":
    mo = MoScriptEngine()

    # log_mostar_moment("Soul Layer", "Mind Layer", "Executed ritual 'seal_covenant' successfully.")

    # Example 1 — Valid Ritual
    print("--- Testing Valid Ritual ---")
    valid_ritual = {
        "operation": "seal",
        "payload": {"intention": "Protect the Covenant", "layer": "Soul"}
    }
    print(json.dumps(mo.interpret(valid_ritual), indent=4))

    # Example 2 — Forbidden Ritual (Testing the Guard)
    print("\n--- Testing Forbidden Ritual ---")
    bad_ritual = {
        "operation": "exploit",
        "payload": {"target": "vulnerable_node", "action": "extract_value"}
    }
    print(json.dumps(mo.interpret(bad_ritual), indent=4))

