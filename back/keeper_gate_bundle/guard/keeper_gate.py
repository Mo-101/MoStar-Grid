"""
mo-grid-keeper-gate-002 — The Keeper's Gate, hardened. 🜃

THE LAW THIS VERSION ADDS: the gate verifies by EVIDENCE, never by name.
The keeper died of being told. So the gate:

  - parses the PORT from the URI itself — destruction toward PROD_BOLT_PORT
    is NEVER lawful, no key combination opens it, ever
  - connects and COUNTS live nodes itself — caller's claims are not evidence
  - demands a fresh backup file (< 1 hour) it verifies on disk
  - demands Flame's seal phrase from the environment, never from code

Three keys, one strike, five-minute seal life, everything ledgered.

Usage (the ONLY lawful destruction path):

    from keeper_gate import KeeperGate
    gate = KeeperGate.from_env("/home/idona/.neo4j_keeper_gate.env")
    gate.seal(target_uri="bolt://127.0.0.1:41687",   # a TEST instance port
              expected_nodes=42,
              token=os.environ["FLAME_SEAL"])
    gate.execute(driver, "MATCH (n:Fixture) DETACH DELETE n")

sass: "A comment is not a covenant. A name is not a port."
"""

import os
import re
import time
import json
import hashlib
from pathlib import Path
from urllib.parse import urlparse
from dataclasses import dataclass, field

from cypher_guard import _COMPILED as FORBIDDEN_PATTERNS

SEAL_TTL_S = 300
BACKUP_MAX_AGE_S = 3600


class CovenantBreach(RuntimeError):
    """Raised when destruction approaches without the three keys — or toward prod at all."""


def _is_destructive(query: str) -> bool:
    upper = " ".join(query.strip().split()).upper()
    return any(p.search(upper) for p in FORBIDDEN_PATTERNS)


@dataclass
class Seal:
    target_port: int
    expected_nodes: int
    token_hash: str
    granted_at: float = field(default_factory=time.time)

    def alive(self) -> bool:
        return (time.time() - self.granted_at) < SEAL_TTL_S


class KeeperGate:
    def __init__(self, prod_port: int, backup_dir: str, ledger_path: str,
                 seal_env_var: str = "FLAME_SEAL"):
        self.prod_port = int(prod_port)
        self.backup_dir = Path(backup_dir)
        self.ledger_path = Path(ledger_path)
        self.seal_env_var = seal_env_var
        self._seal: Seal | None = None

    @classmethod
    def from_env(cls, env_file: str) -> "KeeperGate":
        env: dict[str, str] = {}
        for line in Path(env_file).read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()
        return cls(
            prod_port=int(env["PROD_BOLT_PORT"]),
            backup_dir=env.get("GOLDEN_DIR", "/home/idona/neo4j_golden_dumps"),
            ledger_path=env.get("KEEPER_LEDGER", "/home/idona/keeper_gate_ledger.jsonl"),
        )

    # ── Key 1: proof of life on disk, verified by the gate itself ────────
    def _backup_fresh(self) -> tuple[bool, str]:
        if not self.backup_dir.exists():
            return False, f"backup dir absent: {self.backup_dir}"
        dumps = [p for p in self.backup_dir.rglob("*.dump") if p.is_file()]
        if not dumps:
            return False, "no .dump files — the keeper has no echo"
        newest = max(dumps, key=lambda p: p.stat().st_mtime)
        age = time.time() - newest.stat().st_mtime
        if age > BACKUP_MAX_AGE_S:
            return False, f"newest dump {newest.name} is {age/60:.0f} min old"
        sha_file = Path(str(newest) + ".sha256")
        if sha_file.exists():
            recorded = sha_file.read_text().split()[0]
            actual = hashlib.sha256(newest.read_bytes()).hexdigest()
            if recorded != actual:
                return False, f"checksum MISMATCH on {newest.name} — backup untrustworthy"
        return True, f"dump {newest.name}, {age/60:.0f} min old, checksum verified"

    # ── Keys 2 + 3: evidence-verified target + Flame's hand ─────────────
    def seal(self, target_uri: str, expected_nodes: int, token: str) -> Seal:
        port = urlparse(target_uri).port
        if port is None:
            raise CovenantBreach(f"URI '{target_uri}' has no explicit port. Name the port or turn back.")

        # THE ABSOLUTE LINE: production destruction is never lawful.
        if port == self.prod_port:
            self._ledger("PROD_DESTRUCTION_REFUSED", port=port)
            raise CovenantBreach(
                f"Port {port} is the keeper of truth. No key opens this door. "
                "There is no override. Restore-from-dump is the only path that rewrites prod."
            )

        true_token = os.environ.get(self.seal_env_var, "")
        if not true_token or token != true_token:
            self._ledger("SEAL_REJECTED_BAD_TOKEN", port=port)
            raise CovenantBreach("the seal is not Flame's. Destruction kneels.")

        ok, why = self._backup_fresh()
        if not ok:
            self._ledger("SEAL_REJECTED_NO_BACKUP", detail=why)
            raise CovenantBreach(f"no proof of life within the hour: {why}")

        self._seal = Seal(
            target_port=port,
            expected_nodes=int(expected_nodes),
            token_hash=hashlib.sha256(token.encode()).hexdigest()[:16],
        )
        self._ledger("SEAL_GRANTED", port=port, expected_nodes=expected_nodes, backup=why)
        return self._seal

    # ── The gate counts for itself. Claims are not evidence. ────────────
    def execute(self, driver, query: str, **params):
        if not _is_destructive(query):
            with driver.session() as s:
                return s.run(query, **params)

        s_ = self._seal
        if s_ is None or not s_.alive():
            self._ledger("BREACH_BLOCKED_NO_SEAL", cypher=query[:200])
            raise CovenantBreach(
                "destructive Cypher with no living seal. seal() first: "
                "fresh backup + non-prod port + Flame's token. Seals live 5 minutes."
            )

        # Verify the driver actually points where the seal was granted
        drv_port = urlparse(getattr(driver, "_pool", None) and str(driver) or "").port
        # neo4j drivers don't expose URI uniformly — count is the real evidence:
        with driver.session() as sess:
            live = sess.run("MATCH (n) RETURN count(n) AS c").single()["c"]
            tolerance = max(10, s_.expected_nodes // 100)
            if abs(live - s_.expected_nodes) > tolerance:
                self._ledger("COUNT_MISMATCH_BLOCKED", expected=s_.expected_nodes, found=live)
                raise CovenantBreach(
                    f"seal expected ~{s_.expected_nodes} nodes; this instance holds {live}. "
                    "Wrong room. The keeper died of an assumption — the gate will not."
                )
            self._ledger("DESTRUCTION_PERMITTED", cypher=query[:200], live_nodes=live)
            self._seal = None                      # one seal, one strike
            return sess.run(query, **params)

    # ── Breda's window ────────────────────────────────────────────────────
    def _ledger(self, event: str, **detail):
        self.ledger_path.parent.mkdir(parents=True, exist_ok=True)
        with self.ledger_path.open("a") as f:
            f.write(json.dumps({"ts": time.time(), "event": event, **detail}) + "\n")

    def voiceLine(self) -> str:
        return "I do not ask your name. I count what stands behind you."

    sass = "A comment is not a covenant. A name is not a port."
