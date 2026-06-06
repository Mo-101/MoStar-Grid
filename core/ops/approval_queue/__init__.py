"""Persistent approval queue for Phase 4.0a canon ingestion."""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Optional

from grid.config import APPROVAL_QUEUE_PATH, MOSTAR_CLUSTER_ID


class ProposalState(str, Enum):
    PROPOSED = "PROPOSED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    REVISED = "REVISED"
    COMMITTED = "COMMITTED"


@dataclass
class ProposalRecord:
    id: str
    state: ProposalState
    canon_input: str
    interpretation: dict
    consistency: dict
    placement: dict
    proposed_mutations: list[dict]
    proposed_at: str
    cluster_id: str = MOSTAR_CLUSTER_ID
    approved_by: Optional[str] = None
    approved_at: Optional[str] = None
    rejected_reason: Optional[str] = None
    rejected_at: Optional[str] = None
    parent_id: Optional[str] = None
    version: int = 1
    committed_at: Optional[str] = None
    memory_id: Optional[str] = None
    moment_id: Optional[str] = None
    semantic_frame: Optional[dict] = None

    def to_dict(self) -> dict:
        data = asdict(self)
        data["proposal_id"] = data.pop("id")
        data["state"] = self.state.value
        return data

    @classmethod
    def from_dict(cls, data: dict) -> "ProposalRecord":
        payload = {k: v for k, v in data.items() if not k.startswith("_")}
        if "proposal_id" in payload and "id" not in payload:
            payload["id"] = payload.pop("proposal_id")
        payload.setdefault("cluster_id", MOSTAR_CLUSTER_ID)
        payload["state"] = ProposalState(str(payload["state"]).upper())
        return cls(**payload)


class ApprovalQueue:
    """Append-only JSONL state store for human approval decisions."""

    def __init__(self, path: Path | None = None):
        self.path = path or APPROVAL_QUEUE_PATH
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._records: dict[str, ProposalRecord] = {}
        self.load()

    def load(self) -> None:
        self._records = {}
        if not self.path.exists():
            return
        with open(self.path, "r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                line = line.strip()
                if not line:
                    continue
                try:
                    record = ProposalRecord.from_dict(json.loads(line))
                except Exception as exc:
                    raise ValueError(
                        f"Approval queue corrupted at {self.path}:{line_number}: {exc}"
                    ) from exc
                self._records[record.id] = record

    async def enqueue(self, proposal: ProposalRecord) -> str:
        self._records[proposal.id] = proposal
        self._append(proposal, "enqueue")
        return proposal.id

    async def approve(self, proposal_id: str, approved_by: str) -> ProposalRecord:
        record = await self.get(proposal_id)
        self._assert_transition(record, {ProposalState.PROPOSED}, "approve")
        record.state = ProposalState.APPROVED
        record.approved_by = approved_by
        record.approved_at = _now()
        self._append(record, "approve")
        return record

    async def reject(self, proposal_id: str, reason: str) -> ProposalRecord:
        record = await self.get(proposal_id)
        self._assert_transition(record, {ProposalState.PROPOSED, ProposalState.APPROVED}, "reject")
        record.state = ProposalState.REJECTED
        record.rejected_reason = reason
        record.rejected_at = _now()
        self._append(record, "reject")
        return record

    async def revise(self, proposal_id: str, corrections: str) -> ProposalRecord:
        parent = await self.get(proposal_id)
        self._assert_transition(parent, {ProposalState.PROPOSED, ProposalState.REJECTED}, "revise")
        parent.state = ProposalState.REVISED
        self._append(parent, "revise_parent")

        revised = ProposalRecord(
            id=new_proposal_id(),
            state=ProposalState.PROPOSED,
            canon_input=corrections,
            interpretation={},
            consistency={},
            placement={},
            proposed_mutations=[],
            proposed_at=_now(),
            parent_id=parent.id,
            version=parent.version + 1,
        )
        self._records[revised.id] = revised
        self._append(revised, "revise_child")
        return revised

    async def replace(self, proposal: ProposalRecord, transition: str) -> ProposalRecord:
        self._records[proposal.id] = proposal
        self._append(proposal, transition)
        return proposal

    async def get(self, proposal_id: str) -> ProposalRecord:
        try:
            return self._records[proposal_id]
        except KeyError as exc:
            raise KeyError(f"Proposal not found: {proposal_id}") from exc

    async def list_pending(self) -> list[ProposalRecord]:
        return [
            record for record in self._records.values()
            if record.state == ProposalState.PROPOSED
        ]

    async def list_all(self, limit: int = 50) -> list[ProposalRecord]:
        records = sorted(self._records.values(), key=lambda r: r.proposed_at, reverse=True)
        return records[:limit]

    async def stats(self) -> dict:
        today = _now()[:10]
        records = list(self._records.values())
        return {
            "pending": sum(1 for r in records if r.state == ProposalState.PROPOSED),
            "approved_uncommitted": sum(1 for r in records if r.state == ProposalState.APPROVED),
            "committed_today": sum(1 for r in records if r.committed_at and r.committed_at.startswith(today)),
            "rejected_today": sum(1 for r in records if r.rejected_at and r.rejected_at.startswith(today)),
            "total_proposals": len(records),
        }

    def _append(self, proposal: ProposalRecord, transition: str) -> None:
        payload = proposal.to_dict()
        payload["_transition"] = transition
        payload["_transition_at"] = _now()
        with open(self.path, "a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=False) + "\n")

    @staticmethod
    def _assert_transition(record: ProposalRecord, allowed: set[ProposalState], action: str) -> None:
        if record.state not in allowed:
            raise ValueError(f"Cannot {action} proposal {record.id} from state {record.state.value}")


def new_proposal_id() -> str:
    return f"proposal_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S%f')}"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
