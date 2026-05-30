"""
Provenance — Audit Trail
Every Talk→Learn→Remember cycle is logged with full provenance.
"""
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from dataclasses import dataclass, asdict

from grid.config import MOSTAR_CLUSTER_ID, PROVENANCE_PATH, SEAL_GLYPH

logger = logging.getLogger("provenance")


@dataclass
class ProvenanceRecord:
    cycle_id: str
    cluster_id: str
    timestamp: str
    talk_input: str
    dcx_layer: str
    dcx_model: str
    context_nodes: int
    truth_passed: bool
    truth_scores: dict
    woo_approved: bool
    woo_confidence: float
    memory_id: str
    moment_id: str
    seal: str


class ProvenanceLog:
    """Append-only audit log for Grid intelligence cycles."""

    def __init__(self):
        self._log_file = PROVENANCE_PATH
        self._log_file.parent.mkdir(parents=True, exist_ok=True)
        self._records: list[ProvenanceRecord] = []

    def record(self, **kwargs) -> ProvenanceRecord:
        rec = ProvenanceRecord(
            cluster_id=MOSTAR_CLUSTER_ID,
            timestamp=datetime.now(timezone.utc).isoformat(),
            seal=SEAL_GLYPH,
            **kwargs,
        )
        self._records.append(rec)
        # Append to daily log
        try:
            with open(self._log_file, "a") as f:
                f.write(json.dumps(asdict(rec)) + "\n")
        except Exception as e:
            logger.error("Provenance write failed: %s", e)
        logger.info("Provenance: cycle %s sealed", rec.cycle_id)
        return rec

    def record_event(self, event_type: str, payload: dict) -> dict:
        event = {
            "event_type": event_type,
            "cluster_id": MOSTAR_CLUSTER_ID,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "seal": SEAL_GLYPH,
            **payload,
        }
        try:
            with open(self._log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(event, ensure_ascii=False) + "\n")
        except Exception as e:
            logger.error("Provenance event write failed: %s", e)
        logger.info("Provenance event: %s", event_type)
        return event

    @property
    def total_cycles(self) -> int:
        return len(self._records)

    def recent(self, n: int = 10) -> list[dict]:
        return [asdict(r) for r in self._records[-n:]]
