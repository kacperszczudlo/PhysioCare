import asyncio
import json
import threading
import time
from uuid import uuid4

import pytest
from django.test import override_settings
from rest_framework import status

from notifications.sse import get_sse_bus, publish_user_event


@pytest.fixture(autouse=True)
def _clear_sse_bus() -> object:
    """Czyszczenie magistrali zdarzeń SSE przed i po każdym teście."""
    get_sse_bus().clear()
    yield
    get_sse_bus().clear()


def _parse_sse_frames(body: str) -> list[dict[str, object]]:
    """Parsuje surową odpowiedź strumieniową SSE do listy obiektów zdarzeń."""
    frames: list[dict[str, object]] = []
    for block in body.strip().split('\n\n'):
        if not block.strip():
            continue
        if all(line.startswith(':') or not line.strip() for line in block.splitlines()):
            continue
        event_name: str | None = None
        data_raw: str | None = None
        for line in block.splitlines():
            if line.startswith('event:'):
                event_name = line.split(':', 1)[1].strip()
            elif line.startswith('data:'):
                data_raw = line.split(':', 1)[1].strip()
        assert event_name is not None
        assert data_raw is not None
        payload: dict[str, object] = json.loads(data_raw)
        assert payload['type'] == event_name
        frames.append(payload)
    return frames


@pytest.mark.django_db
def test_events_requires_auth(api_client: object) -> None:
    """Sprawdza wymóg autoryzacji dla punktu końcowego transmisji zdarzeń SSE."""
    # Arrange
    response: object = api_client.get('/api/v1/me/events/')
    # Assert
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
@override_settings(SSE_HEARTBEAT_SECONDS=1, SSE_MAX_FRAMES=1)
def test_events_accepts_event_stream_header(api_client: object, patient: object) -> None:
    """Sprawdza akceptację nagłówka text/event-stream i zwrócenie ramek SSE."""
    # Arrange
    api_client.force_authenticate(user=patient.user)
    response: object = api_client.get(
        '/api/v1/me/events/',
        HTTP_ACCEPT='text/event-stream',
    )
    # Assert
    assert response.status_code == status.HTTP_200_OK
    assert response['Content-Type'].startswith('text/event-stream')
    body: str = b''.join(response.streaming_content).decode()
    frames: list[dict[str, object]] = _parse_sse_frames(body)
    assert len(frames) == 1
    assert frames[0]['type'] == 'ping'


@pytest.mark.django_db
@override_settings(SSE_HEARTBEAT_SECONDS=5, SSE_MAX_FRAMES=1)
def test_events_delivers_published_event(api_client: object, therapist: object) -> None:
    """Sprawdza doręczenie opublikowanego zdarzenia SSE w trakcie trwania połączenia HTTP."""
    # Arrange
    user_id: object = therapist.user.pk
    resource_id: object = uuid4()

    def publish_soon() -> None:
        deadline: float = time.time() + 2
        while time.time() < deadline:
            if get_sse_bus().subscriber_count(str(user_id)) > 0:
                publish_user_event(
                    user_id,
                    'visit.scheduled',
                    resource_id=resource_id,
                )
                return
            time.sleep(0.02)
        raise AssertionError('SSE subscriber did not appear in time')

    thread: threading.Thread = threading.Thread(target=publish_soon)
    thread.start()
    api_client.force_authenticate(user=therapist.user)
    response: object = api_client.get(
        '/api/v1/me/events/',
        HTTP_ACCEPT='text/event-stream',
    )
    # Assert
    assert response.status_code == status.HTTP_200_OK
    body: str = b''.join(response.streaming_content).decode()
    thread.join(timeout=5)
    assert not thread.is_alive()

    frames: list[dict[str, object]] = _parse_sse_frames(body)
    assert len(frames) == 1
    assert frames[0]['type'] == 'visit.scheduled'
    assert frames[0]['resource_id'] == str(resource_id)


@pytest.mark.django_db
def test_publish_rejects_unknown_type(patient: object) -> None:
    """Sprawdza odrzucenie próby publikacji nieznanego typu zdarzenia SSE."""
    # Act
    with pytest.raises(ValueError, match='Unknown SSE'):
        publish_user_event(patient.user.pk, 'visit.unknown', resource_id=uuid4())


@pytest.mark.django_db
@override_settings(SSE_HEARTBEAT_SECONDS=1, SSE_MAX_FRAMES=1)
def test_aiter_sse_frames_generates_ping(patient: object) -> None:
    """Sprawdza generowanie pakietu ping przez asynchroniczny generator aiter_sse_frames."""
    # Arrange
    from notifications.sse import aiter_sse_frames

    async def _run() -> str:
        frames_raw: list[str] = []
        async for frame in aiter_sse_frames(str(patient.user.pk)):
            frames_raw.append(frame)
        return ''.join(frames_raw)

    body: str = asyncio.run(_run())
    parsed: list[dict[str, object]] = _parse_sse_frames(body)
    # Assert
    assert len(parsed) == 1
    assert parsed[0]['type'] == 'ping'


@pytest.mark.django_db
@override_settings(SSE_HEARTBEAT_SECONDS=5, SSE_MAX_FRAMES=1)
def test_aiter_sse_frames_delivers_event(therapist: object) -> None:
    """Sprawdza doręczanie zdarzenia przez generator aiter_sse_frames."""
    # Arrange
    from notifications.sse import aiter_sse_frames

    user_id: object = therapist.user.pk
    resource_id: object = uuid4()

    async def run_stream() -> str:
        chunks: list[str] = []
        async for chunk in aiter_sse_frames(str(user_id)):
            chunks.append(chunk)
        return ''.join(chunks)

    def publish_soon() -> None:
        deadline: float = time.time() + 2
        while time.time() < deadline:
            if get_sse_bus().subscriber_count(str(user_id)) > 0:
                publish_user_event(user_id, 'visit.scheduled', resource_id=resource_id)
                return
            time.sleep(0.02)

    thread: threading.Thread = threading.Thread(target=publish_soon)
    thread.start()

    body: str = asyncio.run(run_stream())
    thread.join(timeout=5)
    # Assert
    assert not thread.is_alive()

    parsed: list[dict[str, object]] = _parse_sse_frames(body)
    assert len(parsed) == 1
    assert parsed[0]['type'] == 'visit.scheduled'
    assert parsed[0]['resource_id'] == str(resource_id)


def test_server_sent_event_renderer_render() -> None:
    """Sprawdza renderowanie danych w ServerSentEventRenderer oraz weryfikację typów."""
    # Arrange
    from notifications.renderers import ServerSentEventRenderer

    renderer: ServerSentEventRenderer = ServerSentEventRenderer()
    data: str = "data: test\n\n"
    # Assert
    assert renderer.render(data) == data
    assert renderer.render(data, accepted_media_type="text/event-stream", renderer_context={}) == data
    # Act

    with pytest.raises(TypeError, match="accepted_media_type musi być typu str lub None."):
        renderer.render(data, accepted_media_type=123)

    with pytest.raises(TypeError, match="renderer_context musi być typu dict lub None."):
        renderer.render(data, renderer_context="invalid")




