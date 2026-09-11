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


class AsyncSseSubscriber:
    """Async subscriber holding an asyncio.Queue and its bound event loop."""

    def __init__(self, loop: asyncio.AbstractEventLoop, maxsize: int = _QUEUE_MAXSIZE) -> None:
        self.loop = loop
        self.queue: asyncio.Queue[SseEvent] = asyncio.Queue(maxsize=maxsize)

    def put_nowait(self, event: SseEvent) -> bool:
        def _put():
            try:
                self.queue.put_nowait(event)
            except asyncio.QueueFull:
                pass

        if self.loop.is_running():
            self.loop.call_soon_threadsafe(_put)
            return True
        return False


class InMemorySseBus:
    """Single-process in-memory SSE bus supporting both sync and async subscribers."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._subscribers: dict[str, list[Queue[SseEvent]]] = {}
        self._async_subscribers: dict[str, list[AsyncSseSubscriber]] = {}
        self._published_total: int = 0
        self._dropped_total: int = 0

    def subscribe(self, user_id: str) -> Queue[SseEvent]:
        queue: Queue[SseEvent] = Queue(maxsize=_QUEUE_MAXSIZE)
        with self._lock:
            self._subscribers.setdefault(user_id, []).append(queue)
        return queue

    def subscribe_async(self, user_id: str) -> asyncio.Queue[SseEvent]:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.get_event_loop()
        sub = AsyncSseSubscriber(loop=loop, maxsize=_QUEUE_MAXSIZE)
        with self._lock:
            self._async_subscribers.setdefault(user_id, []).append(sub)
        return sub.queue

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

    def unsubscribe_async(self, user_id: str, queue: asyncio.Queue[SseEvent]) -> None:
        with self._lock:
            subs = self._async_subscribers.get(user_id)
            if not subs:
                return
            to_remove = [s for s in subs if s.queue is queue]
            for s in to_remove:
                try:
                    subs.remove(s)
                except ValueError:
                    pass
            if not subs:
                del self._async_subscribers[user_id]

    def publish(self, user_id: str, event: SseEvent) -> int:
        with self._lock:
            self._published_total += 1
            sync_queues = list(self._subscribers.get(user_id, ()))
            async_subs = list(self._async_subscribers.get(user_id, ()))
        delivered = 0
        for queue in sync_queues:
            try:
                queue.put_nowait(event)
                delivered += 1
            except Full:
                with self._lock:
                    self._dropped_total += 1
        for sub in async_subs:
            if sub.put_nowait(event):
                delivered += 1
            else:
                with self._lock:
                    self._dropped_total += 1
        return delivered

    def subscriber_count(self, user_id: str) -> int:
        with self._lock:
            sync_cnt = len(self._subscribers.get(user_id, ()))
            async_cnt = len(self._async_subscribers.get(user_id, ()))
            return sync_cnt + async_cnt

    def active_streams_count(self) -> int:
        with self._lock:
            sync_total = sum(len(qs) for qs in self._subscribers.values())
            async_total = sum(len(subs) for subs in self._async_subscribers.values())
            return sync_total + async_total

    def active_users_count(self) -> int:
        with self._lock:
            keys = set(self._subscribers.keys()) | set(self._async_subscribers.keys())
            return len(keys)

    def get_metrics(self) -> dict[str, Any]:
        return {
            'engine': 'inmemory',
            'active_streams': self.active_streams_count(),
            'active_users': self.active_users_count(),
            'total_published': self._published_total,
            'total_dropped': self._dropped_total,
            'redis_listener_alive': None,
        }

    def clear(self) -> None:
        with self._lock:
            self._subscribers.clear()
            self._async_subscribers.clear()
            self._published_total = 0
            self._dropped_total = 0


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

    def subscribe_async(self, user_id: str) -> asyncio.Queue[SseEvent]:
        self._ensure_listener()
        return self._local_bus.subscribe_async(user_id)

    def unsubscribe(self, user_id: str, queue: Queue[SseEvent]) -> None:
        self._local_bus.unsubscribe(user_id, queue)

    def unsubscribe_async(self, user_id: str, queue: asyncio.Queue[SseEvent]) -> None:
        self._local_bus.unsubscribe_async(user_id, queue)

    def is_redis_listener_alive(self) -> bool:
        return self._pubsub_thread is not None and self._pubsub_thread.is_alive()

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

    def active_streams_count(self) -> int:
        return self._local_bus.active_streams_count()

    def active_users_count(self) -> int:
        return self._local_bus.active_users_count()

    def get_metrics(self) -> dict[str, Any]:
        metrics = self._local_bus.get_metrics()
        metrics['engine'] = 'redis'
        metrics['redis_listener_alive'] = self.is_redis_listener_alive()
        return metrics

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


def get_sse_metrics() -> dict[str, Any]:
    """Returns current SSE bus performance and connection metrics."""
    return get_sse_bus().get_metrics()


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
    """Async SSE generator for ASGI execution using native asyncio.Queue (non-blocking)."""
    bus = get_sse_bus()
    queue = bus.subscribe_async(user_id)
    heartbeat = max(1, int(getattr(settings, 'SSE_HEARTBEAT_SECONDS', 20)))
    max_frames = int(getattr(settings, 'SSE_MAX_FRAMES', 0) or 0)
    frames = 0
    try:
        yield ': connected\n\n'
        while True:
            if max_frames and frames >= max_frames:
                break
            try:
                event = await asyncio.wait_for(queue.get(), timeout=heartbeat)
            except asyncio.TimeoutError:
                event = SseEvent(type='ping', resource_id=None, at=timezone.now())
            yield format_sse_frame(event)
            frames += 1
    finally:
        bus.unsubscribe_async(user_id, queue)

