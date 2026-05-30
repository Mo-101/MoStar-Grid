"""Signed dispute notice registration and access checks."""
from __future__ import annotations

import json
import secrets
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from federation.crypto import canonical_bytes, verify_ed25519
from federation.keys import ClusterKeyRegistry, UnknownClusterKeyError
from grid.config import CLUSTER_DIR, MOSTAR_CLUSTER_ID


VALID_REASONS = {
    "anomaly_detected",
    "insufficient_evidence",
    "governance_violation",
    "quality_concern",
    "timeline_mismatch",
    "other",
}
VALID_SEVERITIES = {"low", "medium", "high"}
ACTIVE_STATUSES = {"active"}


class DisputeError(ValueError):
    pass


class InvalidDisputeSignature(DisputeError):
    pass


class InvalidDisputeReason(DisputeError):
    pass


class InvalidDisputeStatus(DisputeError):
    pass


class DisputeLog:
    def __init__(
        self,
        cluster_dir: Path | None = None,
        key_registry: ClusterKeyRegistry | None = None,
    ):
        self.cluster_dir = cluster_dir or CLUSTER_DIR
        self.path = self.cluster_dir / "disputes_received.jsonl"
        self.cluster_dir.mkdir(parents=True, exist_ok=True)
        self.key_registry = key_registry or ClusterKeyRegistry()

    def register_dispute(self, payload: dict[str, Any]) -> dict[str, Any]:
        notice = self._normalize(payload)
        self._validate_notice(notice)
        self._verify_signature(notice)

        existing = self.find_active_dispute(
            scroll_id=notice["scroll_id"],
            disputing_cluster_id=notice["disputing_cluster_id"],
            now=_parse_time(notice["registered_at"]),
        )
        if existing:
            return {
                "dispute_id": existing["dispute_id"],
                "status": existing["status"],
                "created": False,
                "expires_at": existing["expires_at"],
            }

        self._append(notice)
        return {
            "dispute_id": notice["dispute_id"],
            "status": notice["status"],
            "created": True,
            "expires_at": notice["expires_at"],
        }

    def can_access_evidence(
        self,
        *,
        cluster_id: str,
        scroll_id: str,
        now: datetime | None = None,
    ) -> bool:
        return self.find_active_dispute(scroll_id, cluster_id, now=now) is not None

    def active_dispute(
        self,
        *,
        cluster_id: str,
        scroll_id: str,
        now: datetime | None = None,
    ) -> dict[str, Any] | None:
        return self.find_active_dispute(scroll_id, cluster_id, now=now)

    def can_finalize_scroll(self, scroll_id: str) -> bool:
        now = datetime.now(timezone.utc)
        for dispute in self.read_disputes_received():
            if (
                dispute["scroll_id"] == scroll_id
                and dispute["severity"] == "high"
                and dispute["status"] == "active"
                and _parse_time(dispute["expires_at"]) > now
            ):
                return False
        return True

    def find_active_dispute(
        self,
        scroll_id: str,
        disputing_cluster_id: str,
        now: datetime | None = None,
    ) -> dict[str, Any] | None:
        now = now or datetime.now(timezone.utc)
        for dispute in self.read_disputes_received():
            if (
                dispute["scroll_id"] == scroll_id
                and dispute["disputing_cluster_id"] == disputing_cluster_id
                and dispute["status"] == "active"
                and _parse_time(dispute["expires_at"]) > now
            ):
                return dispute
        return None

    def read_disputes_received(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        with open(self.path, "r", encoding="utf-8") as handle:
            return [json.loads(line) for line in handle if line.strip()]

    def _normalize(self, payload: dict[str, Any]) -> dict[str, Any]:
        notice = dict(payload)
        now = _now()
        notice.setdefault("dispute_id", _new_dispute_id())
        notice.setdefault("status", "active")
        notice.setdefault("registered_at", now)
        notice.setdefault("expires_at", _format_time(_parse_time(notice["registered_at"]) + timedelta(days=30)))
        return notice

    def _validate_notice(self, notice: dict[str, Any]) -> None:
        required = {
            "dispute_id",
            "scroll_id",
            "disputing_cluster_id",
            "reason",
            "details",
            "severity",
            "status",
            "registered_at",
            "expires_at",
            "signature",
        }
        missing = sorted(required - set(notice))
        if missing:
            raise DisputeError(f"missing_dispute_fields: {missing}")
        if notice["reason"] not in VALID_REASONS:
            raise InvalidDisputeReason(notice["reason"])
        if notice["severity"] not in VALID_SEVERITIES:
            raise DisputeError(f"invalid_dispute_severity: {notice['severity']}")
        if notice["status"] != "active":
            raise InvalidDisputeStatus(notice["status"])
        if _parse_time(notice["expires_at"]) <= _parse_time(notice["registered_at"]):
            raise DisputeError("dispute_expiration_must_be_after_registration")

    def _verify_signature(self, notice: dict[str, Any]) -> None:
        try:
            public_key = self.key_registry.get_public_key(notice["disputing_cluster_id"])
        except UnknownClusterKeyError as exc:
            raise InvalidDisputeSignature("unknown_disputing_cluster_key") from exc
        if not verify_ed25519(
            public_key,
            notice["signature"],
            dispute_signing_bytes(notice),
        ):
            raise InvalidDisputeSignature("invalid_dispute_signature")

    def _append(self, notice: dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.path, "a", encoding="utf-8") as handle:
            handle.write(json.dumps(notice, ensure_ascii=False, sort_keys=True) + "\n")


def dispute_signing_bytes(payload: dict[str, Any]) -> bytes:
    unsigned = {k: v for k, v in payload.items() if k != "signature"}
    return canonical_bytes(unsigned)


def _new_dispute_id() -> str:
    return f"dsp-{MOSTAR_CLUSTER_ID}-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}-{secrets.token_hex(3)}"


def _now() -> str:
    return _format_time(datetime.now(timezone.utc))


def _format_time(value: datetime) -> str:
    return value.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _parse_time(value: str) -> datetime:
    normalized = value.replace("Z", "+00:00")
    return datetime.fromisoformat(normalized).astimezone(timezone.utc)
