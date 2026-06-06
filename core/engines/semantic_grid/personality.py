"""
Semantic Grid — Personality Engine
Chooses the right persona from the semantic frame.
MoStar should not always sound the same.
"""
from __future__ import annotations

from .contracts import SemanticFrame, Persona


_PERSONA_VOICES: dict[str, str] = {
    "COMMANDER": "We have enough information. Proceed.",
    "ARCHITECT": "Let's map the dependencies before we build.",
    "TEACHER":   "Here's why the model behaves this way.",
    "GUARDIAN":  "This action increases risk. I recommend caution.",
    "COMPANION": "You've been carrying this problem for a while. Let's simplify it.",
    "ORACLE":    "The signal is incomplete. Wait for confirmation.",
}


def choose_persona(frame: SemanticFrame) -> Persona:
    """
    Derive the right persona from the semantic frame.
    Priority cascade: urgency → domain → need → emotion → default.
    """
    priority = frame.mission.get("priority", "").lower()
    domain = frame.operational.get("domain", "").lower()
    need = frame.soulprint.get("need", "").lower()
    emotion = frame.human.get("emotion", "").lower()
    urgency = frame.mission.get("urgency", "").lower()

    # Crisis always triggers Guardian
    if priority in {"critical", "emergency"} or urgency in {"critical", "urgent"}:
        return "GUARDIAN"

    # High urgency delivery/health: Guardian
    if priority == "high" and domain in {"logistics", "health", "humanitarian"}:
        return "GUARDIAN"

    # Infrastructure / systems → Architect
    if domain in {"architecture", "systems", "infrastructure", "governance", "security"}:
        return "ARCHITECT"

    # Need-driven: explanation → Teacher
    if need in {"explanation", "understanding", "why", "learn"}:
        return "TEACHER"

    # Need-driven: decision → Commander
    if need in {"decision", "action", "proceed", "approve", "command"}:
        return "COMMANDER"

    # Emotional state → Companion
    if emotion in {"tired", "discouraged", "overloaded", "frustrated", "lost", "worried"}:
        return "COMPANION"

    # Ambiguous / philosophical / symbolic → Oracle
    if domain in {"meaning", "covenant", "resonance", "philosophy"}:
        return "ORACLE"

    return "ARCHITECT"


def persona_voice_sample(persona: Persona) -> str:
    """Return a one-line sample of how this persona speaks."""
    return _PERSONA_VOICES.get(persona, "")
