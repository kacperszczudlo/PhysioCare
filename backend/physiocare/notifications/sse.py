"""In-memory per-user SSE fan-out (single process)."""

from __future__ import annotations

import asyncio
import json
import threading
from collections.abc import AsyncIterator, Iterator
from dataclasses import dataclass
from datetime import datetime
from queue import Empty, Full, Queue
from typing import Any
from uuid import UUID

from django.conf import settings
from django.utils import timezone

ALLOWED_EVENT_TYPES = frozenset(
    {
        'visit.scheduled',
        'visit.rescheduled',
        'visit.cancelled',
        'visit.approved',
        'visit.rejected',
        'document.created',
        'exercise.assigned',
        'ping',
    }
)

_QUEUE_MAXSIZE = 64


@dataclass(frozen=True)
class SseEvent:
    type: str
    resource_id: str | None
    at: datetime

    def to_payload(self) -> dict[str, Any]:
        return {
            'type': self.type,
            'resource_id': self.resource_id,
            'at': self.at.isoformat(),
        }


def format_sse_frame(event: SseEvent) -> str:
    payload = json.dumps(event.to_payload(), ensure_ascii=False, separators=(',', ':'))
    return f'event: {event.type}\ndata: {payload}\n\n'


class InMemorySseBus:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._subscribers: dict[str, list[Queue[SseEvent]]] = {}

    def subscribe(self, user_id: str) -> Queue[SseEvent]:
        queue: Queue[SseEvent] = Queue(maxsize=_QUEUE_MAXSIZE)
        with self._lock:
            self._subscribers.setdefault(user_id, []).append(queue)
        return queue

    def unsubscribe(self, user_id: str, queue: Queue[SseEvent]) -> None:
        with self._lock:
            queues = self._subscribers.get(user_id)
            if not queues:
                return
            try:
                queues.remove(queue)
            except ValueError:
                return
            if not queues:
                del self._subscribers[user_id]

    def publish(self, user_id: str, event: SseEvent) -> int:
        with self._lock:
            queues = list(self._subscribers.get(user_id, ()))
        delivered = 0
        for queue in queues:
            try:
                queue.put_nowait(event)
                delivered += 1
            except Full:
                continue
        return delivered

    def subscriber_count(self, user_id: str) -> int:
        with self._lock:
            return len(self._subscribers.get(user_id, ()))

    def clear(self) -> None:
        with self._lock:
            self._subscribers.clear()


_bus = InMemorySseBus()


def get_sse_bus() -> InMemorySseBus:
    return _bus


def publish_user_event(
    user_id: str | UUID | int,
    event_type: str,
    *,
    resource_id: str | UUID | None = None,
    at: datetime | None = None,
) -> int:
    """Publish to all open streams for ``user_id``. Returns subscriber deliveries."""
    if event_type not in ALLOWED_EVENT_TYPES:
        raise ValueError(f'Unknown SSE event type: {event_type}')
    rid = None if event_type == 'ping' or resource_id is None else str(resource_id)
    event = SseEvent(
        type=event_type,
        resource_id=rid,
        at=at or timezone.now(),
    )
    return get_sse_bus().publish(str(user_id), event)


def iter_sse_frames(user_id: str) -> Iterator[str]:
    bus = get_sse_bus()
    queue = bus.subscribe(user_id)
    heartbeat = max(1, int(getattr(settings, 'SSE_HEARTBEAT_SECONDS', 20)))
    max_frames = int(getattr(settings, 'SSE_MAX_FRAMES', 0) or 0)
    frames = 0
    try:
        # Immediate flush for proxies; SSE comment line, not a domain event.
        yield ': connected\n\n'
        while True:
            if max_frames and frames >= max_frames:
                break
            try:
                event = queue.get(timeout=heartbeat)
            except Empty:
                event = SseEvent(type='ping', resource_id=None, at=timezone.now())
            yield format_sse_frame(event)
            frames += 1
    finally:
        bus.unsubscribe(user_id, queue)


async def aiter_sse_frames(user_id: str) -> AsyncIterator[str]:
    """Async SSE generator for ASGI execution (non-blocking for uvicorn event loop)."""
    bus = get_sse_bus()
    queue = bus.subscribe(user_id)
    heartbeat = max(1, int(getattr(settings, 'SSE_HEARTBEAT_SECONDS', 20)))
    max_frames = int(getattr(settings, 'SSE_MAX_FRAMES', 0) or 0)
    frames = 0
    try:
        yield ': connected\n\n'
        while True:
            if max_frames and frames >= max_frames:
                break
            try:
                event = await asyncio.to_thread(queue.get, True, heartbeat)
            except Empty:
                event = SseEvent(type='ping', resource_id=None, at=timezone.now())
            yield format_sse_frame(event)
            frames += 1
    finally:
        bus.unsubscribe(user_id, queue)

