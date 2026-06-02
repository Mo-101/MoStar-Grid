import asyncio
import uuid
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Callable, Awaitable, List

logger = logging.getLogger("grid_events")

class GridEvent:
    def __init__(
        self,
        type: str,
        severity: str,
        mood: str,
        source: str,
        text: str,
        payload: dict,
        source_type: str = "runtime_generated",
        verification_status: str = "unverified",
        operational_trust: str = "reference",
        created_by: str | None = None,
        source_id: str | None = None,
    ):
        self.id = uuid.uuid4().hex
        self.type = type
        self.severity = severity
        self.mood = mood
        self.source = source
        self.text = text
        self.payload = payload
        self.source_type = source_type
        self.verification_status = verification_status
        self.operational_trust = operational_trust
        self.created_by = created_by or source
        self.source_id = source_id
        self.created_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self):
        return {
            "id": self.id,
            "type": self.type,
            "severity": self.severity,
            "mood": self.mood,
            "source": self.source,
            "text": self.text,
            "payload": self.payload,
            "source_type": self.source_type,
            "verification_status": self.verification_status,
            "operational_trust": self.operational_trust,
            "created_by": self.created_by,
            "source_id": self.source_id,
            "created_at": self.created_at
        }


class EventBus:
    def __init__(self):
        self._queues: List[asyncio.Queue] = []
        self._history: List[GridEvent] = []

    def subscribe(self) -> asyncio.Queue:
        q = asyncio.Queue()
        self._queues.append(q)
        return q

    def unsubscribe(self, q: asyncio.Queue):
        if q in self._queues:
            self._queues.remove(q)

    async def publish(self, event: GridEvent):
        self._history.append(event)
        # Keep recent history manageable
        if len(self._history) > 1000:
            self._history.pop(0)
            
        logger.info(f"Published Event: {event.type} [{event.severity}] from {event.source}")
        
        for q in self._queues:
            await q.put(event)

# Global singleton event bus
event_bus = EventBus()
