"""Evidence access gateway for disputed scrolls."""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from federation.crypto import verify_ed25519
from federation.disputes import DisputeLog
from federation.keys import ClusterKeyRegistry, UnknownClusterKeyError
from grid.config import EVIDENCE_DIR


class EvidenceAccessError(PermissionError):
    status_code = 403


class EvidenceUnauthorized(EvidenceAccessError):
    status_code = 401


class EvidenceForbidden(EvidenceAccessError):
    status_code = 403


class EvidenceNotFound(FileNotFoundError):
    status_code = 404


class EvidenceRateLimited(EvidenceAccessError):
    status_code = 429


@dataclass
class EvidenceReference:
    evidence_hash: str
    content_type: str
    size_bytes: int
    timestamp: str
    retrieval_url: str


class EvidenceStore:
    def __init__(self, evidence_dir: Path | None = None):
        self.evidence_dir = evidence_dir or EVIDENCE_DIR
        self.evidence_dir.mkdir(parents=True, exist_ok=True)

    def write_manifest(self, scroll_id: str, evidence: list[dict[str, Any]]) -> Path:
        path = self._manifest_path(scroll_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as handle:
            json.dump({"scroll_id": scroll_id, "evidence": evidence}, handle, ensure_ascii=False, sort_keys=True)
        return path

    def read_manifest(self, scroll_id: str) -> list[dict[str, Any]]:
        path = self._manifest_path(scroll_id)
        if not path.exists():
            raise EvidenceNotFound("evidence_not_found")
        with open(path, "r", encoding="utf-8") as handle:
            payload = json.load(handle)
        return payload.get("evidence", [])

    def _manifest_path(self, scroll_id: str) -> Path:
        return self.evidence_dir / scroll_id / "manifest.json"


class EvidenceRateLimiter:
    def __init__(self, max_requests: int = 60, window_seconds: int = 3600):
        self.max_requests = max_requests
        self.window = timedelta(seconds=window_seconds)
        self._requests: dict[str, list[datetime]] = {}

    def allow(self, cluster_id: str, now: datetime | None = None) -> bool:
        now = now or datetime.now(timezone.utc)
        history = [
            ts for ts in self._requests.get(cluster_id, [])
            if now - ts < self.window
        ]
        if len(history) >= self.max_requests:
            self._requests[cluster_id] = history
            return False
        history.append(now)
        self._requests[cluster_id] = history
        return True


class EvidenceGateway:
    def __init__(
        self,
        *,
        dispute_log: DisputeLog | None = None,
        evidence_store: EvidenceStore | None = None,
        key_registry: ClusterKeyRegistry | None = None,
        rate_limiter: EvidenceRateLimiter | None = None,
    ):
        self.dispute_log = dispute_log or DisputeLog()
        self.evidence_store = evidence_store or EvidenceStore()
        self.key_registry = key_registry or ClusterKeyRegistry()
        self.rate_limiter = rate_limiter or EvidenceRateLimiter()

    def get_evidence(
        self,
        *,
        scroll_id: str,
        requester_cluster_id: str,
        signature: str,
    ) -> dict[str, Any]:
        self._verify_requester(scroll_id, requester_cluster_id, signature)
        if not self.rate_limiter.allow(requester_cluster_id):
            raise EvidenceRateLimited("evidence_rate_limited")
        dispute = self.dispute_log.active_dispute(
            cluster_id=requester_cluster_id,
            scroll_id=scroll_id,
        )
        if not dispute:
            raise EvidenceForbidden("no_active_dispute_for_scroll")
        evidence = self.evidence_store.read_manifest(scroll_id)
        return {
            "scroll_id": scroll_id,
            "evidence": evidence,
            "dispute_id": dispute["dispute_id"],
            "access_expires_at": dispute["expires_at"],
        }

    def _verify_requester(self, scroll_id: str, requester_cluster_id: str, signature: str) -> None:
        try:
            public_key = self.key_registry.get_public_key(requester_cluster_id)
        except UnknownClusterKeyError as exc:
            raise EvidenceUnauthorized("unknown_requester_cluster_key") from exc
        if not verify_ed25519(public_key, signature, scroll_id.encode("utf-8")):
            raise EvidenceUnauthorized("invalid_requester_signature")
