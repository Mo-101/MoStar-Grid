"""Scroll import/export verification pipeline."""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from federation.attestations import AttestationLog, AttestationRecord
from federation.crypto import blake3_hex
from federation.scrolls import Scroll
from grid.config import MOSTAR_CLUSTER_ID


HEX_64 = re.compile(r"^[0-9a-f]{64}$")


class ScrollImportError(ValueError):
    pass


@dataclass
class ScrollImportResult:
    scroll_id: str
    cluster_id: str
    source_cluster_id: str
    scroll_hash: str
    status: str
    ready_for_attestation: bool
    next_step: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "scroll_id": self.scroll_id,
            "cluster_id": self.cluster_id,
            "source_cluster_id": self.source_cluster_id,
            "scroll_hash": self.scroll_hash,
            "status": self.status,
            "ready_for_attestation": self.ready_for_attestation,
            "next_step": self.next_step,
        }


class ScrollImporter:
    def __init__(self, attestation_log: AttestationLog | None = None):
        self.attestation_log = attestation_log or AttestationLog()

    def import_scroll(
        self,
        scroll_payload: dict[str, Any],
        *,
        evidence_blobs: dict[str, str] | None = None,
    ) -> ScrollImportResult:
        try:
            scroll = Scroll.from_dict(scroll_payload)
        except Exception as exc:
            raise ScrollImportError(f"invalid_scroll_payload: {exc}") from exc

        if scroll.cluster.cluster_id == MOSTAR_CLUSTER_ID:
            raise ScrollImportError("cannot_import_local_cluster_scroll")
        if not scroll.verify_cluster_signature():
            raise ScrollImportError("invalid_scroll_signature")

        self._validate_evidence_hashes(scroll)
        if evidence_blobs is not None:
            self._verify_evidence_blobs(scroll, evidence_blobs)

        signature = scroll.seal.cluster_signatures[0]
        record = AttestationRecord.create(
            scroll_id=scroll.scroll_id,
            peer_cluster_id=scroll.cluster.cluster_id,
            signature=signature,
            scroll_hash=scroll.seal.seal_hash,
            status="accepted",
            direction="received",
            scroll=scroll.to_dict(),
        )
        self.attestation_log.record_received(record)

        return ScrollImportResult(
            scroll_id=scroll.scroll_id,
            cluster_id=MOSTAR_CLUSTER_ID,
            source_cluster_id=scroll.cluster.cluster_id,
            scroll_hash=scroll.seal.seal_hash,
            status="imported",
            ready_for_attestation=True,
            next_step="cluster_b_can_now_sign_and_attest",
        )

    @staticmethod
    def _validate_evidence_hashes(scroll: Scroll) -> None:
        for evidence_hash in scroll.evidence.evidence_hashes:
            if not HEX_64.match(evidence_hash):
                raise ScrollImportError(f"invalid_evidence_hash: {evidence_hash}")

    @staticmethod
    def _verify_evidence_blobs(scroll: Scroll, evidence_blobs: dict[str, str]) -> None:
        expected = set(scroll.evidence.evidence_hashes)
        supplied = {blake3_hex(blob) for blob in evidence_blobs.values()}
        missing = expected - supplied
        if missing:
            raise ScrollImportError(f"evidence_hash_mismatch: {sorted(missing)}")
