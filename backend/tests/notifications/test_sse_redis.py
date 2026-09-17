import time

import pytest
from django.test import override_settings
from django.utils import timezone

from notifications.sse import (
    InMemorySseBus,
    RedisPubSubSseBus,
    SseEvent,
    get_sse_bus,
    reset_sse_bus,
)


class MockPubSub:
    """Mock kanału pubsub w Redis dla celów testowych."""

    def __init__(self, mock_redis: object) -> None:
        self.mock_redis: object = mock_redis
        self.messages: list[dict[str, object]] = []
        self.subscribed_pattern: str | None = None

    def psubscribe(self, pattern: str) -> None:
        self.subscribed_pattern = pattern
        self.mock_redis.pubsubs.append(self)

    def get_message(
        self, ignore_subscribe_messages: bool = True, timeout: float = 1.0
    ) -> dict[str, object] | None:
        start: float = time.time()
        while time.time() - start < timeout:
            if self.messages:
                return self.messages.pop(0)
            time.sleep(0.01)
        return None


class MockRedis:
    """Mock klienta Redis dla celów testowych."""

    def __init__(self) -> None:
        self.pubsubs: list[MockPubSub] = []
        self.published: list[tuple[str, str]] = []

    def pubsub(self) -> MockPubSub:
        return MockPubSub(self)

    def publish(self, channel: str, payload: str) -> int:
        self.published.append((channel, payload))
        for ps in list(self.pubsubs):
            ps.messages.append(
                {
                    'type': 'pmessage',
                    'channel': channel,
                    'data': payload,
                }
            )
        return len(self.pubsubs)


@pytest.fixture(autouse=True)
def _reset_bus() -> object:
    """Resetuje magistralę zdarzeń SSE przed i po każdym teście."""
    reset_sse_bus()
    yield
    reset_sse_bus()


def test_get_sse_bus_inmemory() -> None:
    """Sprawdza domyślny wybór silnika in-memory dla magistrali SSE."""
    # Act
    with override_settings(SSE_BUS_ENGINE='inmemory'):
        bus: object = get_sse_bus()
        assert isinstance(bus, InMemorySseBus)


def test_get_sse_bus_redis_selection() -> None:
    """Sprawdza wybór silnika Redis Pub/Sub dla magistrali SSE po ustawieniu flagi w konfiguracji."""
    # Act
    with override_settings(SSE_BUS_ENGINE='redis', _REDIS_URL='redis://localhost:6379/0'):
        bus: object = get_sse_bus()
        assert isinstance(bus, RedisPubSubSseBus)


def test_redis_pubsub_bus_publish_and_receive() -> None:
    """Sprawdza publikowanie i odbiór komunikatów SSE za pośrednictwem Redis Pub/Sub."""
    # Arrange
    mock_r: MockRedis = MockRedis()
    bus: RedisPubSubSseBus = RedisPubSubSseBus(redis_client=mock_r, channel_prefix='test:sse:')
    user_id: str = 'user-123'
    queue: object = bus.subscribe(user_id)

    time.sleep(0.05)

    event: SseEvent = SseEvent(type='visit.scheduled', resource_id='v-1', at=timezone.now())
    bus.publish(user_id, event)

    # Assert
    assert len(mock_r.published) == 1
    channel: str
    # Act
    payload: str
    channel, payload = mock_r.published[0]
    assert channel == 'test:sse:user-123'

    received_event: object = queue.get(timeout=2.0)
    assert received_event.type == 'visit.scheduled'
    assert received_event.resource_id == 'v-1'

    bus.clear()


def test_redis_pubsub_bus_fallback_on_redis_error() -> None:
    """Sprawdza wycofanie się (fallback) do lokalnej magistrali pamięciowej przy awarii połączenia z Redisem."""
    # Arrange
    class FailingRedis:
        def publish(self, channel: str, payload: str) -> int:
            raise RuntimeError('Redis connection error')

    bus: RedisPubSubSseBus = RedisPubSubSseBus(redis_client=FailingRedis(), channel_prefix='test:sse:')
    user_id: str = 'user-fallback'
    queue: object = bus.subscribe(user_id)

    event: SseEvent = SseEvent(type='document.created', resource_id='doc-1', at=timezone.now())
    bus.publish(user_id, event)

    received_event: object = queue.get(timeout=1.0)
    # Assert
    assert received_event.type == 'document.created'
    assert received_event.resource_id == 'doc-1'

    bus.clear()

