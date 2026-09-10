"""In-memory per-user SSE fan-out (single process) and Redis Pub/Sub fan-out (multi-worker)."""

from __future__ import annotations

import asyncio
import json
import os
import threading
import time
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
    """Single-process in-memory SSE bus."""

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


class RedisPubSubSseBus:
    """Multi-process SSE bus backed by Redis Pub/Sub with local in-memory fanout."""

    def __init__(
        self,
        redis_client: Any = None,
        channel_prefix: str | None = None,
    ) -> None:
        self._local_bus = InMemorySseBus()
        self._redis_client = redis_client
        self._channel_prefix = (
            channel_prefix
            if channel_prefix is not None
            else getattr(settings, 'SSE_REDIS_CHANNEL_PREFIX', 'physiocare:sse:')
        )
        self._pubsub_thread: threading.Thread | None = None
        self._stop_event = threading.Event()

    def _get_redis(self) -> Any:
        if self._redis_client is None:
            import redis

            redis_url = getattr(settings, '_REDIS_URL', '') or os.environ.get('REDIS_URL', '').strip()
            if not redis_url:
                raise ValueError('REDIS_URL is not configured for RedisPubSubSseBus')
            self._redis_client = redis.Redis.from_url(redis_url)
        return self._redis_client

    def _ensure_listener(self) -> None:
        if self._pubsub_thread is not None and self._pubsub_thread.is_alive():
            return
        self._stop_event.clear()
        self._pubsub_thread = threading.Thread(
            target=self._listen_loop,
            name='sse-redis-pubsub-listener',
            daemon=True,
        )
        self._pubsub_thread.start()

    def _listen_loop(self) -> None:
        pattern = f'{self._channel_prefix}*'
        prefix_len = len(self._channel_prefix)
        while not self._stop_event.is_set():
            try:
                r = self._get_redis()
                pubsub = r.pubsub()
                pubsub.psubscribe(pattern)
                while not self._stop_event.is_set():
                    msg = pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                    if msg and msg.get('type') == 'pmessage':
                        channel = msg['channel']
                        if isinstance(channel, bytes):
                            channel = channel.decode('utf-8')
                        data = msg['data']
                        if isinstance(data, bytes):
                            data = data.decode('utf-8')
                        user_id = channel[prefix_len:]
                        try:
                            payload = json.loads(data)
                            event = SseEvent(
                                type=payload['type'],
                                resource_id=payload.get('resource_id'),
                                at=datetime.fromisoformat(payload['at']),
                            )
                            self._local_bus.publish(user_id, event)
                        except Exception:
                            pass
            except Exception:
                time.sleep(1.0)

    def subscribe(self, user_id: str) -> Queue[SseEvent]:
        self._ensure_listener()
        return self._local_bus.subscribe(user_id)

    def unsubscribe(self, user_id: str, queue: Queue[SseEvent]) -> None:
        self._local_bus.unsubscribe(user_id, queue)

    def publish(self, user_id: str, event: SseEvent) -> int:
        channel = f'{self._channel_prefix}{user_id}'
        payload = json.dumps(event.to_payload(), ensure_ascii=False, separators=(',', ':'))
        try:
            r = self._get_redis()
            r.publish(channel, payload)
            return self.subscriber_count(user_id)
        except Exception:
            return self._local_bus.publish(user_id, event)

    def subscriber_count(self, user_id: str) -> int:
        return self._local_bus.subscriber_count(user_id)

    def clear(self) -> None:
        self._stop_event.set()
        if self._pubsub_thread and self._pubsub_thread.is_alive():
            self._pubsub_thread.join(timeout=1.0)
        self._local_bus.clear()


_inmemory_bus: InMemorySseBus | None = None
_redis_bus: RedisPubSubSseBus | None = None


def get_sse_bus() -> InMemorySseBus | RedisPubSubSseBus:
    global _inmemory_bus, _redis_bus
    engine = getattr(settings, 'SSE_BUS_ENGINE', 'auto').lower()
    redis_url = getattr(settings, '_REDIS_URL', '') or os.environ.get('REDIS_URL', '').strip()

    if engine == 'redis' or (engine == 'auto' and redis_url):
        if _redis_bus is None:
            _redis_bus = RedisPubSubSseBus()
        return _redis_bus

    if _inmemory_bus is None:
        _inmemory_bus = InMemorySseBus()
    return _inmemory_bus


def reset_sse_bus() -> None:
    global _inmemory_bus, _redis_bus
    if _redis_bus is not None:
        _redis_bus.clear()
        _redis_bus = None
    if _inmemory_bus is not None:
        _inmemory_bus.clear()
        _inmemory_bus = None


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
