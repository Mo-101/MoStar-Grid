"""
MoScript — Sovereign Contract Execution
Event-driven modular intelligence with personality.

Pattern: mo-[domain]-[descriptor]-[number]
Format: {id, name, trigger, inputs, logic(), voiceLine(), sass}
"""
import logging
from dataclasses import dataclass, field
from typing import Callable, Any, Optional

logger = logging.getLogger("moscript")


@dataclass
class MoScript:
    id: str              # mo-grid-heartbeat-001
    name: str            # Heartbeat Check
    trigger: str         # on_startup | on_query | on_learn | on_schedule
    inputs: list[str]    # ["system_state"]
    logic: Callable      # the actual function
    voice_line: str      # what Mo says when it fires
    sass: str            # personality
    enabled: bool = True

    def fire(self, context: dict) -> dict:
        if not self.enabled:
            return {"fired": False, "reason": "disabled"}
        try:
            result = self.logic(context)
            logger.info("MoScript %s fired: %s", self.id, self.voice_line)
            return {
                "fired": True,
                "id": self.id,
                "name": self.name,
                "result": result,
                "voice": self.voice_line,
            }
        except Exception as e:
            logger.error("MoScript %s failed: %s — %s", self.id, e, self.sass)
            return {"fired": False, "error": str(e), "sass": self.sass}


class MoScriptEngine:
    """Registry and executor for MoScript contracts."""

    def __init__(self, enforcement_hook: Optional[Callable] = None):
        self._scripts: dict[str, MoScript] = {}
        self._enforcement_hook = enforcement_hook
        self._register_builtins()

    def register(self, script: MoScript):
        self._scripts[script.id] = script
        logger.info("MoScript registered: %s", script.id)

    def fire_trigger(self, trigger: str, context: dict) -> list[dict]:
        """Fire all scripts matching a trigger."""
        results = []
        for script in self._scripts.values():
            if script.trigger == trigger and script.enabled:
                if self._enforcement_hook is not None:
                    self._enforcement_hook(script, trigger, context)
                results.append(script.fire(context))
        return results

    def list_scripts(self) -> list[dict]:
        return [
            {"id": s.id, "name": s.name, "trigger": s.trigger, "enabled": s.enabled}
            for s in self._scripts.values()
        ]

    def _register_builtins(self):
        """Core MoScripts that ship with the Grid."""

        from core.ops.runtime_attestation import execute_grid_heartbeat

        self.register(MoScript(
            id="mo-grid-heartbeat-001",
            name="Grid Heartbeat",
            trigger="on_startup",
            inputs=["verifier", "runtime_health"],
            logic=execute_grid_heartbeat,
            voice_line="Grid heartbeat evaluated. Only the seal may grant readiness.",
            sass="If you can hear this, something's working.",
        ))

        from core.ops.runtime_attestation import execute_grid_identity

        self.register(MoScript(
            id="mo-grid-identity-002",
            name="Grid Identity",
            trigger="on_startup",
            inputs=["verifier"],
            logic=execute_grid_identity,
            voice_line="Grid identity reported.",
            sass="Attest me no claims I did not make.",
        ))

        self.register(MoScript(
            id="mo-grid-learn-003",
            name="Learn Trigger",
            trigger="on_learn",
            inputs=["content", "category"],
            logic=lambda ctx: {"learned": ctx.get("content", "")[:100]},
            voice_line="New knowledge absorbed into the Graph.",
            sass="Feed me more.",
        ))

        self.register(MoScript(
            id="mo-grid-truth-004",
            name="Truth Gate Monitor",
            trigger="on_query",
            inputs=["truth_verdict"],
            logic=lambda ctx: {
                "gate_status": "open" if ctx.get("truth_passed", False) else "blocked",
                "scores": ctx.get("truth_scores", {}),
            },
            voice_line="Truth Gate evaluated. Elements weighed.",
            sass="Nothing gets past me without passing through fire.",
        ))
