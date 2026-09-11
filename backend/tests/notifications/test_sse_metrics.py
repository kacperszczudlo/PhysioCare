import asyncio
import time
import pytest
from django.test import override_settings
from rest_framework import status

from notifications.sse import (
    InMemorySseBus,
    RedisPubSubSseBus,
    SseEvent,
    aiter_sse_frames,
    get_sse_bus,
    get_sse_metrics,
    publish_user_event,
    reset_sse_bus,
)


@pytest.fixture(autouse=True)
def _reset_bus():
    reset_sse_bus()
    yield
    reset_sse_bus()


def test_inmemory_bus_metrics_tracking():
    bus = InMemorySseBus()
    user1 = 'user-1'
    user2 = 'user-2'

    assert bus.active_streams_count() == 0
    assert bus.active_users_count() == 0

    q1_sync = bus.subscribe(user1)
    assert bus.active_streams_count() == 1
    assert bus.active_users_count() == 1

    async def _sub_async():
        q1_async = bus.subscribe_async(user1)
        q2_async = bus.subscribe_async(user2)
        assert bus.active_streams_count() == 3
        assert bus.active_users_count() == 2

        metrics = bus.get_metrics()
        assert metrics['engine'] == 'inmemory'
        assert metrics['active_streams'] == 3
        assert metrics['active_users'] == 2
        assert metrics['redis_listener_alive'] is None

        bus.unsubscribe_async(user1, q1_async)
        bus.unsubscribe_async(user2, q2_async)

    asyncio.run(_sub_async())
    assert bus.active_streams_count() == 1
    assert bus.active_users_count() == 1

    bus.unsubscribe(user1, q1_sync)
    assert bus.active_streams_count() == 0
    assert bus.active_users_count() == 0


def test_published_and_dropped_metrics():
    bus = InMemorySseBus()
    user = 'user-drop'
    q = bus.subscribe(user)

    event = SseEvent(type='ping', resource_id=None, at=pytest.importorskip('django.utils.timezone').now())
    bus.publish(user, event)

    metrics = bus.get_metrics()
    assert metrics['total_published'] == 1
    assert metrics['total_dropped'] == 0

    bus.unsubscribe(user, q)


@pytest.mark.django_db
def test_sse_stats_api_requires_auth(api_client):
    response = api_client.get('/api/v1/me/events/stats/')
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_sse_stats_api_returns_metrics(api_client, patient):
    api_client.force_authenticate(user=patient.user)
    response = api_client.get('/api/v1/me/events/stats/')
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert 'engine' in data
    assert 'active_streams' in data
    assert 'active_users' in data
    assert 'total_published' in data
    assert 'total_dropped' in data


@pytest.mark.django_db
@override_settings(SSE_HEARTBEAT_SECONDS=1, SSE_MAX_FRAMES=1)
def test_aiter_sse_frames_async_metrics_increment(patient):
    user_id = str(patient.user.pk)

    async def _run():
        assert get_sse_metrics()['active_streams'] == 0
        gen = aiter_sse_frames(user_id)
        first_chunk = await gen.__anext__()
        assert first_chunk == ': connected\n\n'
        assert get_sse_metrics()['active_streams'] == 1
        assert get_sse_metrics()['active_users'] == 1

        ping_frame = await gen.__anext__()
        assert 'event: ping' in ping_frame

        with pytest.raises(StopAsyncIteration):
            await gen.__anext__()

    asyncio.run(_run())
    assert get_sse_metrics()['active_streams'] == 0
    assert get_sse_metrics()['active_users'] == 0

