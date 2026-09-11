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
    def __init__(self, mock_redis) -> None:
        self.mock_redis = mock_redis
        self.messages = []
        self.subscribed_pattern = None

    def psubscribe(self, pattern: str) -> None:
        self.subscribed_pattern = pattern
        self.mock_redis.pubsubs.append(self)

    def get_message(
        self, ignore_subscribe_messages: bool = True, timeout: float = 1.0
    ) -> dict | None:
        start = time.time()
        while time.time() - start < timeout:
            if self.messages:
                return self.messages.pop(0)
            time.sleep(0.01)
        return None


class MockRedis:
    def __init__(self) -> None:
        self.pubsubs = []
        self.published = []

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
def _reset_bus():
    reset_sse_bus()
    yield
    reset_sse_bus()


def test_get_sse_bus_inmemory():
    with override_settings(SSE_BUS_ENGINE='inmemory'):
        bus = get_sse_bus()
        assert isinstance(bus, InMemorySseBus)


def test_get_sse_bus_redis_selection():
    with override_settings(SSE_BUS_ENGINE='redis', _REDIS_URL='redis://localhost:6379/0'):
        bus = get_sse_bus()
        assert isinstance(bus, RedisPubSubSseBus)


def test_redis_pubsub_bus_publish_and_receive():
    mock_r = MockRedis()
    bus = RedisPubSubSseBus(redis_client=mock_r, channel_prefix='test:sse:')
    user_id = 'user-123'
    queue = bus.subscribe(user_id)

    # Allow listener thread time to start and subscribe
    time.sleep(0.05)

    event = SseEvent(type='visit.scheduled', resource_id='v-1', at=timezone.now())
    bus.publish(user_id, event)

    assert len(mock_r.published) == 1
    channel, payload = mock_r.published[0]
    assert channel == 'test:sse:user-123'

    received_event = queue.get(timeout=2.0)
    assert received_event.type == 'visit.scheduled'
    assert received_event.resource_id == 'v-1'

    bus.clear()


def test_redis_pubsub_bus_fallback_on_redis_error():
    class FailingRedis:
        def publish(self, channel, payload: str) -> int:
            raise RuntimeError('Redis connection error')

    bus = RedisPubSubSseBus(redis_client=FailingRedis(), channel_prefix='test:sse:')
    user_id = 'user-fallback'
    queue = bus.subscribe(user_id)

    event = SseEvent(type='document.created', resource_id='doc-1', at=timezone.now())
    bus.publish(user_id, event)

    received_event = queue.get(timeout=1.0)
    assert received_event.type == 'document.created'
    assert received_event.resource_id == 'doc-1'

    bus.clear()
