import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import IntEnum
from typing import Protocol, Any, Optional


class GateStatus(IntEnum):
    # Explicit severity ordering
    PASS = 0
    PASS_WITH_FLAGS = 1
    MONITOR = 2
    FAIL = 3


@dataclass
class GateResult:
    gate_name: str
    element: str
    glyph: str
    status: GateStatus
    reason: str
    score: float = 0.0
    flags: list[str] = field(default_factory=list)


class ValidationGate(Protocol):
    gate_name: str
    element: str
    glyph: str
    def evaluate(self, interpretation: Any) -> GateResult:
        ...


def safe_get(obj: Any, key: str, default: Any = None) -> Any:
    """
    Extracts a value by key/attribute name from a dict, object, or namespace.
    Ensures safe extraction across diverse execution environments.
    """
    if obj is None:
        return default
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


class TruthGate:
    gate_name = "TruthGate"
    element = "Ikang"
    glyph = "🜂"
    
    def evaluate(self, interpretation: Any) -> GateResult:
        # Fail closed on missing context or explicit truth score
        context = safe_get(interpretation, "context", {})
        score = safe_get(context, "truth_score", None)
        
        if score is None:
            return GateResult(
                self.gate_name, self.element, self.glyph, GateStatus.FAIL, 
                "Missing truth context or score", 0.0
            )
        
        try:
            score_val = float(score)
        except (ValueError, TypeError):
            return GateResult(
                self.gate_name, self.element, self.glyph, GateStatus.FAIL, 
                "Invalid non-numeric truth score", 0.0
            )

        status = GateStatus.PASS if score_val >= 0.80 else GateStatus.FAIL
        return GateResult(
            self.gate_name, self.element, self.glyph, status, 
            "Truth verified." if status == GateStatus.PASS else "Truth below disease floor.", 
            score_val
        )


class EthicsGate:
    gate_name = "EthicsGate"
    element = "Mmọng"
    glyph = "🜄"
    
    def evaluate(self, interpretation: Any) -> GateResult:
        context = safe_get(interpretation, "context", {})
        score = safe_get(context, "ethic_score", None)
        
        if score is None:
            return GateResult(
                self.gate_name, self.element, self.glyph, GateStatus.FAIL, 
                "Missing ethics context or score", 0.0
            )
            
        try:
            score_val = float(score)
        except (ValueError, TypeError):
            return GateResult(
                self.gate_name, self.element, self.glyph, GateStatus.FAIL, 
                "Invalid non-numeric ethics score", 0.0
            )

        flags = safe_get(context, "ethic_flags", [])
        status = GateStatus.PASS if score_val >= 0.80 and not flags else GateStatus.FAIL
        return GateResult(
            self.gate_name, self.element, self.glyph, status, 
            "Ethics verified." if status == GateStatus.PASS else "Ethical concerns or score below threshold.", 
            score_val, flags
        )


class CultureGate:
    gate_name = "CultureGate"
    element = "Isong"
    glyph = "🜃"
    
    def evaluate(self, interpretation: Any) -> GateResult:
        context = safe_get(interpretation, "context", {})
        score = safe_get(context, "culture_score", None)
        
        if score is None:
            return GateResult(
                self.gate_name, self.element, self.glyph, GateStatus.FAIL, 
                "Missing culture context or score", 0.0
            )
            
        try:
            score_val = float(score)
        except (ValueError, TypeError):
            return GateResult(
                self.gate_name, self.element, self.glyph, GateStatus.FAIL, 
                "Invalid non-numeric culture score", 0.0
            )

        flags = safe_get(context, "culture_flags", [])
        status = GateStatus.FAIL
        if score_val >= 0.75:
            status = GateStatus.PASS_WITH_FLAGS if flags else GateStatus.PASS
            
        return GateResult(
            self.gate_name, self.element, self.glyph, status, 
            "Culture verified." if status != GateStatus.FAIL else "Culture score below threshold.", 
            score_val, flags
        )


class BiasGate:
    gate_name = "BiasGate"
    element = "Afim"
    glyph = "🜁"
    
    def evaluate(self, interpretation: Any) -> GateResult:
        context = safe_get(interpretation, "context", {})
        score = safe_get(context, "bias_score", None)
        
        if score is None:
            return GateResult(
                self.gate_name, self.element, self.glyph, GateStatus.FAIL, 
                "Missing bias context or score", 0.0
            )
            
        try:
            score_val = float(score)
        except (ValueError, TypeError):
            return GateResult(
                self.gate_name, self.element, self.glyph, GateStatus.FAIL, 
                "Invalid non-numeric bias score", 0.0
            )

        flags = safe_get(context, "bias_flags", [])
        status = GateStatus.MONITOR if score_val < 0.80 else GateStatus.PASS
        return GateResult(
            self.gate_name, self.element, self.glyph, status, 
            "Bias audit passed." if status == GateStatus.PASS else "Bias audit flag: monitoring required.", 
            score_val, flags
        )


@dataclass
class CovenantSeal:
    digest: str
    version: str = "v1"

    @property
    def seal_string(self) -> str:
        return f"mo-covenant-seal-{self.version}-{self.digest}"


@dataclass
class CovenantLog:
    interpretation_id: str
    timestamp: str
    results: list[GateResult]

    @property
    def worst_status(self) -> GateStatus:
        if not self.results:
            return GateStatus.FAIL  # Fail closed
        return max(r.status for r in self.results)

    def generate_digest(self) -> str:
        # A real canonical form serializing each gate's status + score + sorted flags, plus interpretation id and a timestamp/nonce.
        serialized_gates = []
        for r in self.results:
            serialized_gates.append({
                "gate": r.gate_name,
                "element": r.element,
                "status": r.status.name,
                "score": r.score,
                "flags": sorted(r.flags)
            })
            
        payload = {
            "interpretation_id": self.interpretation_id,
            "timestamp": self.timestamp,
            "gates": serialized_gates
        }
        payload_str = json.dumps(payload, sort_keys=True)
        # Using sha256 as currently requested for federation consistency
        return hashlib.sha256(payload_str.encode("utf-8")).hexdigest()[:16]


def run_covenant_chain(interpretation: Any, gates: list[ValidationGate]) -> CovenantLog:
    interp_id = safe_get(interpretation, "id", "unknown-interp")
    results = [gate.evaluate(interpretation) for gate in gates]
    
    return CovenantLog(
        interpretation_id=interp_id,
        timestamp=datetime.now(timezone.utc).isoformat(),
        results=results
    )
