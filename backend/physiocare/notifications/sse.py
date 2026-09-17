from __future__ import annotations

import asyncio
import contextlib
import json
import os
import threading
import time
import logging
from collections.abc import AsyncIterator, Iterator
from dataclasses import dataclass
from datetime import datetime
from queue import Empty, Full, Queue
from uuid import UUID

from django.conf import settings
from django.utils import timezone

logger: logging.Logger = logging.getLogger('physiocare.notifications')


ALLOWED_EVENT_TYPES: set[str] = set(
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

_QUEUE_MAXSIZE: int = 64


@dataclass(frozen=True)
class SseEvent:
    """Struktura zdarzenia SSE przesyłana do klienta."""

    type: str
    resource_id: str | None
    at: datetime

    def to_payload(self) -> dict[str, object]:
        """Konwertuje zdarzenie do postaci słownika z danymi.

        Returns:
            dict[str, object]: Słownik reprezentujący dane zdarzenia.
        """
        return {
            'type': self.type,
            'resource_id': self.resource_id,
            'at': self.at.isoformat(),
        }


def format_sse_frame(event: SseEvent) -> str:
    """Formatuje obiekt zdarzenia do postaci ramki tekstu zgodnej ze specyfikacją SSE.

    Args:
        event (SseEvent): Obiekt zdarzenia.

    Returns:
        str: Tekstowa ramka zdarzenia SSE.
    """
    if not isinstance(event, SseEvent):
        raise TypeError('Argument event musi być instancją SseEvent.')

    payload = json.dumps(event.to_payload(), ensure_ascii=False, separators=(',', ':'))
    return f'event: {event.type}\ndata: {payload}\n\n'


class AsyncSseSubscriber:
    """Subskrybent asynchroniczny przechowujący kolejkę asyncio.Queue oraz pętlę zdarzeń."""

    def __init__(self, loop: asyncio.AbstractEventLoop, maxsize: int = _QUEUE_MAXSIZE) -> None:
        """Inicjalizuje subskrybenta asynchronicznego.

        Args:
            loop (asyncio.AbstractEventLoop): Pętla zdarzeń asyncio.
            maxsize (int): Maksymalny rozmiar kolejki.
        """
        self.loop = loop
        self.queue: asyncio.Queue[SseEvent] = asyncio.Queue(maxsize=maxsize)

    def put_nowait(self, event: SseEvent) -> bool:
        """Wstawia zdarzenie do kolejki asynchronicznej bez blokowania.

        Args:
            event (SseEvent): Zdarzenie SSE.

        Returns:
            bool: True jeśli zdarzenie zostało pomyślnie dodane, False w przeciwnym razie.
        """
        def _put():
            """Wewnętrzny pomocnik dodający zdarzenie do kolejki."""
            with contextlib.suppress(asyncio.QueueFull):
                self.queue.put_nowait(event)

        if self.loop.is_running():
            self.loop.call_soon_threadsafe(_put)
            return True
        return False


class InMemorySseBus:
    """Jednoprocesowa magistrala SSE przechowywana w pamięci operacyjnej."""

    def __init__(self) -> None:
        """Inicjalizuje magistralę lokalną."""
        self._lock = threading.Lock()
        self._subscribers: dict[str, list[Queue[SseEvent]]] = {}
        self._async_subscribers: dict[str, list[AsyncSseSubscriber]] = {}
        self._published_total: int = 0
        self._dropped_total: int = 0

    def subscribe(self, user_id: str) -> Queue[SseEvent]:
        """Rejestruje synchronicznego subskrybenta dla wskazanego użytkownika.

        Args:
            user_id (str): Identyfikator użytkownika.

        Returns:
            Queue[SseEvent]: Kolejka zdarzeń.
        """
        queue: Queue[SseEvent] = Queue(maxsize=_QUEUE_MAXSIZE)
        with self._lock:
            self._subscribers.setdefault(user_id, []).append(queue)
        return queue

    def subscribe_async(self, user_id: str) -> asyncio.Queue[SseEvent]:
        """Rejestruje asynchronicznego subskrybenta.

        Args:
            user_id (str): Identyfikator użytkownika.

        Returns:
            asyncio.Queue[SseEvent]: Kolejka asynchroniczna.
        """
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.get_event_loop()
        sub = AsyncSseSubscriber(loop=loop, maxsize=_QUEUE_MAXSIZE)
        with self._lock:
            self._async_subscribers.setdefault(user_id, []).append(sub)
        return sub.queue

    def unsubscribe(self, user_id: str, queue: Queue[SseEvent]) -> None:
        """Wyrejestrowuje synchronicznego subskrybenta.

        Args:
            user_id (str): Identyfikator użytkownika.
            queue (Queue[SseEvent]): Rejestrowana kolejka.
        """
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
        """Wyrejestrowuje asynchronicznego subskrybenta.

        Args:
            user_id (str): Identyfikator użytkownika.
            queue (asyncio.Queue[SseEvent]): Kolejka asynchroniczna.
        """
        with self._lock:
            subs = self._async_subscribers.get(user_id)
            if not subs:
                return
            to_remove = [s for s in subs if s.queue is queue]
            for s in to_remove:
                with contextlib.suppress(ValueError):
                    subs.remove(s)
            if not subs:
                del self._async_subscribers[user_id]

    def publish(self, user_id: str, event: SseEvent) -> int:
        """Rozsyła zdarzenie do wszystkich subskrybentów danego użytkownika.

        Args:
            user_id (str): Identyfikator odbiorcy.
            event (SseEvent): Obiekt zdarzenia.

        Returns:
            int: Liczba doręczonych zdarzeń.
        """
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
        """Zwraca całkowitą liczbę subskrybentów użytkownika.

        Args:
            user_id (str): Identyfikator użytkownika.

        Returns:
            int: Liczba połączeń.
        """
        with self._lock:
            sync_cnt = len(self._subscribers.get(user_id, ()))
            async_cnt = len(self._async_subscribers.get(user_id, ()))
            return sync_cnt + async_cnt

    def active_streams_count(self) -> int:
        """Zwraca łączną liczbę aktywnych strumieni.

        Returns:
            int: Liczba otwartych strumieni.
        """
        with self._lock:
            sync_total = sum(len(qs) for qs in self._subscribers.values())
            async_total = sum(len(subs) for subs in self._async_subscribers.values())
            return sync_total + async_total

    def active_users_count(self) -> int:
        """Zwraca liczbę unikalnych podłączonych użytkowników.

        Returns:
            int: Liczba aktywnych użytkowników.
        """
        with self._lock:
            keys = set(self._subscribers.keys()) | set(self._async_subscribers.keys())
            return len(keys)

    def get_metrics(self) -> dict[str, object]:
        """Pobiera zbiorcze metryki wydajnościowe magistrali.

        Returns:
            dict[str, object]: Słownik z danymi statystycznymi.
        """
        return {
            'engine': 'inmemory',
            'active_streams': self.active_streams_count(),
            'active_users': self.active_users_count(),
            'total_published': self._published_total,
            'total_dropped': self._dropped_total,
            'redis_listener_alive': None,
        }

    def clear(self) -> None:
        """Resetuje stan magistrali i zamyka subskrypcje."""
        with self._lock:
            self._subscribers.clear()
            self._async_subscribers.clear()
            self._published_total = 0
            self._dropped_total = 0


class RedisPubSubSseBus:
    """Wieloprocesowa magistrala SSE wykorzystująca Redis Pub/Sub."""

    def __init__(
        self,
        redis_client=None,
        channel_prefix: str | None = None,
    ) -> None:
        """Inicjalizuje magistralę Redis Pub/Sub."""
        self._local_bus = InMemorySseBus()
        self._redis_client = redis_client
        self._channel_prefix = (
            channel_prefix
            if channel_prefix is not None
            else (settings.SSE_REDIS_CHANNEL_PREFIX if hasattr(settings, 'SSE_REDIS_CHANNEL_PREFIX') else 'physiocare:sse:')
        )
        self._pubsub_thread: threading.Thread | None = None
        self._stop_event = threading.Event()

    def _get_redis(self) -> object:
        """Pobiera lub inicjalizuje połączenie z klientem Redis.

        Returns:
            object: Klient Redis (redis.Redis).

        Raises:
            ValueError: Gdy adres REDIS_URL nie jest skonfigurowany.
        """
        if self._redis_client is None:
            import redis

            redis_url = (settings._REDIS_URL if hasattr(settings, '_REDIS_URL') else '') or os.environ.get('REDIS_URL', '').strip()
            if not redis_url:
                raise ValueError('Adres REDIS_URL nie został skonfigurowany dla RedisPubSubSseBus')
            self._redis_client = redis.Redis.from_url(redis_url)
        return self._redis_client


    def _ensure_listener(self) -> None:
        """Upewnia się, że wątek nasłuchujący wiadomości z magistrali Redis Pub/Sub działa."""
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
        """Pętla nasłuchująca wiadomości Redis Pub/Sub i przekazująca je do magistrali lokalnej."""
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
                        except Exception as exc:
                            logger.debug('Nieudana parsowanie pakietu SSE z Redis: %s', exc)
            except Exception as exc:
                logger.debug('Błąd w pętli nasłuchującej Redis SSE: %s', exc)
                time.sleep(1.0)


    def subscribe(self, user_id: str) -> Queue[SseEvent]:
        """Rejestruje synchronicznego subskrybenta."""
        self._ensure_listener()
        return self._local_bus.subscribe(user_id)

    def subscribe_async(self, user_id: str) -> asyncio.Queue[SseEvent]:
        """Rejestruje asynchronicznego subskrybenta."""
        self._ensure_listener()
        return self._local_bus.subscribe_async(user_id)

    def unsubscribe(self, user_id: str, queue: Queue[SseEvent]) -> None:
        """Wyrejestrowuje synchronicznego subskrybenta."""
        self._local_bus.unsubscribe(user_id, queue)

    def unsubscribe_async(self, user_id: str, queue: asyncio.Queue[SseEvent]) -> None:
        """Wyrejestrowuje asynchronicznego subskrybenta."""
        self._local_bus.unsubscribe_async(user_id, queue)

    def is_redis_listener_alive(self) -> bool:
        """Sprawdza aktywność wątku nasłuchującego Redis."""
        return self._pubsub_thread is not None and self._pubsub_thread.is_alive()

    def publish(self, user_id: str, event: SseEvent) -> int:
        """Publikuje zdarzenie w kanale Redis Pub/Sub."""
        channel = f'{self._channel_prefix}{user_id}'
        payload = json.dumps(event.to_payload(), ensure_ascii=False, separators=(',', ':'))
        try:
            r = self._get_redis()
            r.publish(channel, payload)
            return self.subscriber_count(user_id)
        except Exception:
            return self._local_bus.publish(user_id, event)

    def subscriber_count(self, user_id: str) -> int:
        """Pobiera liczbę subskrybentów użytkownika."""
        return self._local_bus.subscriber_count(user_id)

    def active_streams_count(self) -> int:
        """Pobiera liczbę aktywnych strumieni."""
        return self._local_bus.active_streams_count()

    def active_users_count(self) -> int:
        """Pobiera liczbę aktywnych użytkowników."""
        return self._local_bus.active_users_count()

    def get_metrics(self) -> dict[str, object]:
        """Zwraca metryki magistrali Redis SSE."""
        metrics = self._local_bus.get_metrics()
        metrics['engine'] = 'redis'
        metrics['redis_listener_alive'] = self.is_redis_listener_alive()
        return metrics

    def clear(self) -> None:
        """Czyści zasoby i wyłącza wątek nasłuchujący."""
        self._stop_event.set()
        if self._pubsub_thread and self._pubsub_thread.is_alive():
            self._pubsub_thread.join(timeout=1.0)
        self._local_bus.clear()


_inmemory_bus: InMemorySseBus | None = None
_redis_bus: RedisPubSubSseBus | None = None


def get_sse_bus() -> InMemorySseBus | RedisPubSubSseBus:
    """Pobiera aktywną instancję magistrali SSE (zależnie od konfiguracji).

    Returns:
        InMemorySseBus | RedisPubSubSseBus: Obiekt magistrali SSE.
    """
    global _inmemory_bus, _redis_bus
    engine_val = settings.SSE_BUS_ENGINE if hasattr(settings, 'SSE_BUS_ENGINE') else 'auto'
    engine = engine_val.lower() if isinstance(engine_val, str) else 'auto'
    redis_url = (settings._REDIS_URL if hasattr(settings, '_REDIS_URL') else '') or os.environ.get('REDIS_URL', '').strip()

    if engine == 'redis' or (engine == 'auto' and redis_url):
        if _redis_bus is None:
            _redis_bus = RedisPubSubSseBus()
        return _redis_bus

    if _inmemory_bus is None:
        _inmemory_bus = InMemorySseBus()
    return _inmemory_bus


def get_sse_metrics() -> dict[str, object]:
    """Zwraca metryki wydajnościowe oraz dane o połączeniach strumienia SSE.

    Returns:
        dict[str, object]: Słownik ze statystykami.
    """
    return get_sse_bus().get_metrics()


def reset_sse_bus() -> None:
    """Resetuje silniki magistrali SSE (przydatne w testach)."""
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
    """Publikuje zdarzenie do wszystkich otwartych strumieni użytkownika.

    Args:
        user_id (str | UUID | int): Identyfikator użytkownika.
        event_type (str): Typ zdarzenia (musi znajdować się w ALLOWED_EVENT_TYPES).
        resource_id (str | UUID | None): Opcjonalny identyfikator zasobu.
        at (datetime | None): Znacznik czasu zdarzenia.

    Returns:
        int: Liczba wysłanych powiadomień do subskrybentów.
    """
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
    """Generator ramek zdarzeń SSE do transmisji synchronicznej.

    Args:
        user_id (str): Identyfikator użytkownika.

    Yields:
        Iterator[str]: Ciągi tekstowe ramek danych SSE.
    """
    bus = get_sse_bus()
    queue = bus.subscribe(user_id)
    hb_val = settings.SSE_HEARTBEAT_SECONDS if hasattr(settings, 'SSE_HEARTBEAT_SECONDS') else 20
    heartbeat = max(1, int(hb_val))
    max_f_val = settings.SSE_MAX_FRAMES if hasattr(settings, 'SSE_MAX_FRAMES') else 0
    max_frames = int(max_f_val or 0)
    frames = 0
    try:
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
    """Asynchroniczny generator ramek zdarzeń SSE dla serwera ASGI.

    Args:
        user_id (str): Identyfikator użytkownika.

    Yields:
        AsyncIterator[str]: Strumień zdarzeń SSE.
    """
    bus = get_sse_bus()
    queue = bus.subscribe_async(user_id)
    hb_val = settings.SSE_HEARTBEAT_SECONDS if hasattr(settings, 'SSE_HEARTBEAT_SECONDS') else 20
    heartbeat = max(1, int(hb_val))
    max_f_val = settings.SSE_MAX_FRAMES if hasattr(settings, 'SSE_MAX_FRAMES') else 0
    max_frames = int(max_f_val or 0)
    frames = 0
    try:
        yield ': connected\n\n'
        while True:
            if max_frames and frames >= max_frames:
                break
            try:
                event = await asyncio.wait_for(queue.get(), timeout=heartbeat)
            except TimeoutError:
                event = SseEvent(type='ping', resource_id=None, at=timezone.now())
            yield format_sse_frame(event)
            frames += 1
    finally:
        bus.unsubscribe_async(user_id, queue)


