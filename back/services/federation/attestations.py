"""Append-only per-cluster attestation logs."""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from grid.config import CLUSTER_DIR, MOSTAR_CLUSTER_ID


@dataclass
class AttestationRecord:
    timestamp: str
    cluster_id: str
    scroll_id: str
    peer_cluster_id: str
    signature: str
    scroll_hash: str
    status: str
    direction: str
    scroll: dict[str, Any] | None = None

    @classmethod
    def create(
        cls,
        *,
        scroll_id: str,
        peer_cluster_id: str,
        signature: str,
        scroll_hash: str,
        status: str,
        direction: str,
        cluster_id: str = MOSTAR_CLUSTER_ID,
        scroll: dict[str, Any] | None = None,
    ) -> "AttestationRecord":
        return cls(
            timestamp=_now(),
            cluster_id=cluster_id,
            scroll_id=scroll_id,
            peer_cluster_id=peer_cluster_id,
            signature=signature,
            scroll_hash=scroll_hash,
            status=status,
            direction=direction,
            scroll=scroll,
        )

    def to_dict(self) -> dict:
        payload = {
            "timestamp": self.timestamp,
            "scroll_id": self.scroll_id,
            "signature": self.signature,
            "status": self.status,
        }
        if self.direction == "given":
            payload["cluster_receiving"] = self.peer_cluster_id
        elif self.direction == "received":
            payload["cluster_attesting"] = self.peer_cluster_id
        else:
            payload["peer_cluster_id"] = self.peer_cluster_id
        payload["cluster_id"] = self.cluster_id
        payload["scroll_hash"] = self.scroll_hash
        payload["direction"] = self.direction
        if self.scroll is not None:
            payload["scroll"] = self.scroll
        return payload


class AttestationLog:
    def __init__(self, cluster_dir: Path | None = None):
        self.cluster_dir = cluster_dir or CLUSTER_DIR
        self.given_path = self.cluster_dir / "attestations_given.jsonl"
        self.received_path = self.cluster_dir / "attestations_received.jsonl"
        self.disputed_path = self.cluster_dir / "disputed_scrolls.jsonl"
        self.cluster_dir.mkdir(parents=True, exist_ok=True)

    def record_given(self, record: AttestationRecord) -> AttestationRecord:
        if record.direction != "given":
            raise ValueError("given attestations must use direction='given'")
        self._append(self.given_path, record)
        return record

    def record_received(self, record: AttestationRecord) -> AttestationRecord:
        if record.direction != "received":
            raise ValueError("received attestations must use direction='received'")
        self._append(self.received_path, record)
        return record

    def record_dispute(self, record: AttestationRecord) -> AttestationRecord:
        if record.status != "disputed":
            raise ValueError("disputed scroll records must use status='disputed'")
        self._append(self.disputed_path, record)
        return record

    def read_given(self) -> list[dict]:
        return self._read(self.given_path)

    def read_received(self) -> list[dict]:
        return self._read(self.received_path)

    def read_disputed(self) -> list[dict]:
        return self._read(self.disputed_path)

    @staticmethod
    def _append(path: Path, record: AttestationRecord) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a", encoding="utf-8") as handle:
            handle.write(json.dumps(record.to_dict(), ensure_ascii=False, sort_keys=True) + "\n")

    @staticmethod
    def _read(path: Path) -> list[dict]:
        if not path.exists():
            return []
        with open(path, "r", encoding="utf-8") as handle:
            return [json.loads(line) for line in handle if line.strip()]


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
