"""
Truth Engine — Elemental Verification Gate
Every response must pass elemental thresholds before it exits the Grid.

Fire (Ikang 🜂)  = 0.75 — Clarity, directness
Water (Mmọng 🜄) = 0.70 — Flow, coherence
Air (Afim 🜁)    = 0.65 — Breath, completeness
Earth (Isong 🜃) = 0.80 — Grounding, factual basis
"""
import logging
from dataclasses import dataclass, field
from grid.config import TRUTH_THRESHOLDS, SEAL_GLYPH

logger = logging.getLogger("truth_engine")


@dataclass
class TruthVerdict:
    passed: bool
    scores: dict[str, float]
    thresholds: dict[str, float]
    failures: list[str] = field(default_factory=list)
    seal: str = ""

    @property
    def summary(self) -> str:
        if self.passed:
            return f"TRUTH GATE PASSED {self.seal}"
        return f"TRUTH GATE FAILED: {', '.join(self.failures)}"


class TruthEngine:
    """Validates responses against elemental thresholds."""

    def __init__(self):
        self.thresholds = TRUTH_THRESHOLDS.copy()

    def evaluate(self, response: str, query: str = "", context_count: int = 0) -> TruthVerdict:
        """
        Score a response across the four elements.
        Uses heuristic scoring — can be upgraded to model-based later.
        """
        scores = {
            "ikang": self._score_ikang(response),
            "mmong": self._score_mmong(response),
            "afim": self._score_afim(response, query),
            "isong": self._score_isong(response, context_count),
        }

        failures = []
        for element, score in scores.items():
            if score < self.thresholds[element]:
                failures.append(
                    f"{element}({score:.2f}<{self.thresholds[element]:.2f})"
                )

        passed = len(failures) == 0
        verdict = TruthVerdict(
            passed=passed,
            scores=scores,
            thresholds=self.thresholds,
            failures=failures,
            seal=SEAL_GLYPH if passed else "",
        )
        if not passed:
            logger.warning("Truth Gate FAILED: %s", verdict.summary)
        return verdict

    async def validate_consistency(
        self,
        proposed_content: str,
        proposed_labels: list[str],
        existing_context: list[dict],
    ) -> TruthVerdict:
        """
        Check proposed canon against nearby graph context.
        This heuristic mode is conservative and can be upgraded to model-based validation.
        """
        content = proposed_content.strip()
        lower_content = content.lower()
        duplicate = False
        contradiction = False
        existing_labels = set()

        for node in existing_context:
            labels = node.get("_labels", [])
            if isinstance(labels, list):
                existing_labels.update(labels)
            node_text = str(node.get("content", node.get("name", ""))).lower()
            if node_text and self._similarity(lower_content, node_text) > 0.85:
                duplicate = True
            if node_text and self._looks_contradictory(lower_content, node_text):
                contradiction = True

        proposed_label_set = set(proposed_labels)
        scores = {
            "ikang": 0.35 if contradiction else 0.9,
            "mmong": min(1.0, 0.65 + len(existing_context) * 0.04),
            "afim": self._score_afim(content, "canon proposal"),
            "isong": 0.85 if not existing_context or proposed_label_set & existing_labels else 0.65,
        }
        if duplicate:
            scores["ikang"] = min(scores["ikang"], 0.7)

        failures = []
        if contradiction:
            failures.append("contradiction_detected")
        if duplicate:
            failures.append("possible_duplicate")
        for element, score in scores.items():
            if score < self.thresholds[element]:
                failures.append(f"{element}({score:.2f}<{self.thresholds[element]:.2f})")

        passed = len(failures) == 0
        return TruthVerdict(
            passed=passed,
            scores=scores,
            thresholds=self.thresholds,
            failures=failures,
            seal=SEAL_GLYPH if passed else "",
        )

    # ── Element Scoring (heuristic v1) ─────────────────────────────

    def _score_ikang(self, response: str) -> float:
        """Fire 🜂 — Clarity and directness. Penalizes vague/filler text."""
        if not response.strip():
            return 0.0

        words = response.split()
        length = len(words)

        # Penalize very short or very long responses
        if length < 3:
            return 0.4
        if length > 2000:
            return 0.6

        # Penalize filler phrases
        filler = ["i think maybe", "it could be", "perhaps", "i'm not sure but",
                   "it depends", "generally speaking", "in some cases"]
        filler_count = sum(1 for f in filler if f in response.lower())
        filler_penalty = min(filler_count * 0.1, 0.3)

        # Reward structured content (code blocks, bullets, clear sentences)
        has_structure = any(c in response for c in ["```", "- ", "1.", "→", ":"])
        structure_bonus = 0.05 if has_structure else 0.0

        return min(1.0, max(0.0, 0.85 - filler_penalty + structure_bonus))

    def _score_mmong(self, response: str) -> float:
        """Water 🜄 — Flow and coherence. Checks sentence connectivity."""
        if not response.strip():
            return 0.0

        sentences = [s.strip() for s in response.replace("\n", ". ").split(".") if s.strip()]
        if len(sentences) <= 1:
            return 0.75  # Single sentence = coherent by default

        # Simple coherence: check that response isn't just random fragments
        avg_sentence_len = sum(len(s.split()) for s in sentences) / len(sentences)
        if avg_sentence_len < 2:
            return 0.5  # Too fragmented
        if avg_sentence_len > 50:
            return 0.6  # Run-on, poor flow

        return min(1.0, 0.75 + (min(avg_sentence_len, 15) / 15) * 0.2)

    def _score_afim(self, response: str, query: str) -> float:
        """Air 🜁 — Completeness. Does the response address the query?"""
        if not response.strip():
            return 0.0
        if not query.strip():
            return 0.75  # No query to compare against

        # Check keyword overlap between query and response
        import re
        clean = lambda s: set(re.findall(r'\w+', s.lower()))
        query_words = clean(query)
        response_words = clean(response)
        # Remove stopwords
        stops = {"the", "a", "an", "is", "are", "was", "were", "do", "does",
                 "what", "how", "why", "can", "will", "i", "you", "me", "my", "it"}
        query_key = query_words - stops
        if not query_key:
            return 0.75

        overlap = len(query_key & response_words) / len(query_key)
        return min(1.0, 0.6 + overlap * 0.35)

    def _score_isong(self, response: str, context_count: int) -> float:
        """Earth 🜃 — Grounding. Is the response backed by graph context?"""
        if not response.strip():
            return 0.0

        # Base score from response substance
        words = len(response.split())
        base = 0.65 if words > 10 else (0.5 if words > 5 else 0.4)

        # Bonus for graph context being used
        if context_count > 0:
            context_bonus = min(context_count * 0.06, 0.3)
        else:
            context_bonus = 0.0

        # Penalize error messages
        if response.startswith("[DCX") or "error" in response.lower()[:50]:
            return 0.3

        return min(1.0, base + context_bonus)

    @staticmethod
    def _similarity(left: str, right: str) -> float:
        import difflib

        return difflib.SequenceMatcher(None, left, right).ratio()

    @staticmethod
    def _looks_contradictory(left: str, right: str) -> bool:
        contradiction_pairs = [
            (" is ", " is not "),
            (" always ", " never "),
            (" enabled", " disabled"),
            (" true", " false"),
        ]
        for positive, negative in contradiction_pairs:
            if positive in left and negative in right:
                return True
            if negative in left and positive in right:
                return True
        return False
