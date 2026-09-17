import asyncio

import pytest
from django.test import override_settings
from rest_framework import status

from notifications.sse import (
    InMemorySseBus,
    SseEvent,
    aiter_sse_frames,
    get_sse_metrics,
    reset_sse_bus,
)


@pytest.fixture(autouse=True)
def _reset_bus() -> object:
    """Resetuje magistralę zdarzeń SSE przed i po każdym teście."""
    reset_sse_bus()
    yield
    reset_sse_bus()


def test_inmemory_bus_metrics_tracking() -> None:
    """Sprawdza zliczanie metryk połączeń (streamów i użytkowników) w InMemorySseBus."""
    # Arrange
    bus: InMemorySseBus = InMemorySseBus()
    user1: str = 'user-1'
    user2: str = 'user-2'

    # Assert
    assert bus.active_streams_count() == 0
    assert bus.active_users_count() == 0

    q1_sync: object = bus.subscribe(user1)
    assert bus.active_streams_count() == 1
    assert bus.active_users_count() == 1

    async def _sub_async() -> None:
        q1_async: object = bus.subscribe_async(user1)
        q2_async: object = bus.subscribe_async(user2)
        assert bus.active_streams_count() == 3
        assert bus.active_users_count() == 2

        metrics: dict[str, object] = bus.get_metrics()
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


def test_published_and_dropped_metrics() -> None:
    """Sprawdza zliczanie liczby opublikowanych i porzuconych komunikatów w metrykach SSE."""
    # Arrange
    bus: InMemorySseBus = InMemorySseBus()
    user: str = 'user-drop'
    q: object = bus.subscribe(user)

    event: SseEvent = SseEvent(type='ping', resource_id=None, at=pytest.importorskip('django.utils.timezone').now())
    bus.publish(user, event)

    metrics: dict[str, object] = bus.get_metrics()
    # Assert
    assert metrics['total_published'] == 1
    assert metrics['total_dropped'] == 0

    bus.unsubscribe(user, q)


@pytest.mark.django_db
def test_sse_stats_api_requires_auth(api_client: object) -> None:
    """Sprawdza wymóg autoryzacji przy próbie pobrania statystyk SSE za pośrednictwem API."""
    # Arrange
    response: object = api_client.get('/api/v1/me/events/stats/')
    # Assert
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_sse_stats_api_returns_metrics(api_client: object, patient: object) -> None:
    """Sprawdza zwracanie metryk i statystyk połączeń SSE dla autoryzowanego użytkownika."""
    # Arrange
    api_client.force_authenticate(user=patient.user)
    response: object = api_client.get('/api/v1/me/events/stats/')
    # Assert
    assert response.status_code == status.HTTP_200_OK
    data: dict[str, object] = response.json()
    assert 'engine' in data
    assert 'active_streams' in data
    assert 'active_users' in data
    assert 'total_published' in data
    assert 'total_dropped' in data


@pytest.mark.django_db
@override_settings(SSE_HEARTBEAT_SECONDS=1, SSE_MAX_FRAMES=1)
def test_aiter_sse_frames_async_metrics_increment(patient: object) -> None:
    """Sprawdza inkrementację metryk podczas asynchronicznego pobierania ramek SSE."""
    # Arrange
    user_id: str = str(patient.user.pk)

    async def _run() -> None:
        assert get_sse_metrics()['active_streams'] == 0
        gen: object = aiter_sse_frames(user_id)
        first_chunk: str = await gen.__anext__()
        assert first_chunk == ': connected\n\n'
        assert get_sse_metrics()['active_streams'] == 1
        assert get_sse_metrics()['active_users'] == 1

        ping_frame: str = await gen.__anext__()
        assert 'event: ping' in ping_frame

        with pytest.raises(StopAsyncIteration):
            await gen.__anext__()

    asyncio.run(_run())
    # Assert
    assert get_sse_metrics()['active_streams'] == 0
    assert get_sse_metrics()['active_users'] == 0


