from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class WooInterpretation:
    prompt: str
    resonance_score: float
    symbolic_state: str
    advisory: str
    evidence: list[str] = field(default_factory=list)


class WooInterpreter:
    states = {
        "genesis": ("begin", "start", "build", "create", "kickoff"),
        "resonance": ("align", "resonate", "seal", "canon", "memory"),
        "covenant": ("approve", "commit", "signature", "govern"),
        "discord": ("risk", "secret", "leak", "contradiction", "unsafe"),
        "fracture": ("bypass", "violate", "corrupt", "expose"),
        "stillness": ("pause", "standby", "review", "wait"),
    }

    def interpret(self, prompt: str) -> WooInterpretation:
        text = prompt.lower()
        hits: dict[str, int] = {}
        evidence: list[str] = []

        for state, words in self.states.items():
            matched = [word for word in words if word in text]
            if matched:
                hits[state] = len(matched)
                evidence.extend(f"{state}:{word}" for word in matched)

        symbolic_state = max(hits, key=hits.get) if hits else "stillness"
        resonance_score = min(1.0, 0.45 + (sum(hits.values()) * 0.08))

        return WooInterpretation(
            prompt=prompt,
            resonance_score=round(resonance_score, 3),
            symbolic_state=symbolic_state,
            advisory=f"Woo advises symbolic state `{symbolic_state}` with confidence {resonance_score:.3f}.",
            evidence=evidence,
        )
