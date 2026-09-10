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
def _clear_sse_bus():
    get_sse_bus().clear()
    yield
    get_sse_bus().clear()


def _parse_sse_frames(body: str) -> list[dict]:
    frames = []
    for block in body.strip().split('\n\n'):
        if not block.strip():
            continue
        # SSE comments (np. ": connected") - pomijamy
        if all(line.startswith(':') or not line.strip() for line in block.splitlines()):
            continue
        event_name = None
        data_raw = None
        for line in block.splitlines():
            if line.startswith('event:'):
                event_name = line.split(':', 1)[1].strip()
            elif line.startswith('data:'):
                data_raw = line.split(':', 1)[1].strip()
        assert event_name is not None
        assert data_raw is not None
        payload = json.loads(data_raw)
        assert payload['type'] == event_name
        frames.append(payload)
    return frames


@pytest.mark.django_db
def test_events_requires_auth(api_client):
    response = api_client.get('/api/v1/me/events/')
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
@override_settings(SSE_HEARTBEAT_SECONDS=1, SSE_MAX_FRAMES=1)
def test_events_accepts_event_stream_header(api_client, patient):
    """EventSource sends Accept: text/event-stream - must not 406."""
    api_client.force_authenticate(user=patient.user)
    response = api_client.get(
        '/api/v1/me/events/',
        HTTP_ACCEPT='text/event-stream',
    )
    assert response.status_code == status.HTTP_200_OK
    assert response['Content-Type'].startswith('text/event-stream')
    body = b''.join(response.streaming_content).decode()
    frames = _parse_sse_frames(body)
    assert len(frames) == 1
    assert frames[0]['type'] == 'ping'


@pytest.mark.django_db
@override_settings(SSE_HEARTBEAT_SECONDS=5, SSE_MAX_FRAMES=1)
def test_events_delivers_published_event(api_client, therapist):
    user_id = therapist.user.pk
    resource_id = uuid4()

    def publish_soon():
        deadline = time.time() + 2
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

    thread = threading.Thread(target=publish_soon)
    thread.start()
    api_client.force_authenticate(user=therapist.user)
    response = api_client.get(
        '/api/v1/me/events/',
        HTTP_ACCEPT='text/event-stream',
    )
    assert response.status_code == status.HTTP_200_OK
    body = b''.join(response.streaming_content).decode()
    thread.join(timeout=5)
    assert not thread.is_alive()

    frames = _parse_sse_frames(body)
    assert len(frames) == 1
    assert frames[0]['type'] == 'visit.scheduled'
    assert frames[0]['resource_id'] == str(resource_id)


@pytest.mark.django_db
def test_publish_rejects_unknown_type(patient):
    with pytest.raises(ValueError, match='Unknown SSE'):
        publish_user_event(patient.user.pk, 'visit.unknown', resource_id=uuid4())


@pytest.mark.django_db
@override_settings(SSE_HEARTBEAT_SECONDS=1, SSE_MAX_FRAMES=1)
def test_aiter_sse_frames_generates_ping(patient):
    from notifications.sse import aiter_sse_frames

    async def _run():
        frames_raw = []
        async for frame in aiter_sse_frames(str(patient.user.pk)):
            frames_raw.append(frame)
        return ''.join(frames_raw)

    body = asyncio.run(_run())
    parsed = _parse_sse_frames(body)
    assert len(parsed) == 1
    assert parsed[0]['type'] == 'ping'


@pytest.mark.django_db
@override_settings(SSE_HEARTBEAT_SECONDS=5, SSE_MAX_FRAMES=1)
def test_aiter_sse_frames_delivers_event(therapist):
    from notifications.sse import aiter_sse_frames

    user_id = therapist.user.pk
    resource_id = uuid4()

    async def run_stream():
        chunks = []
        async for chunk in aiter_sse_frames(str(user_id)):
            chunks.append(chunk)
        return ''.join(chunks)

    def publish_soon():
        deadline = time.time() + 2
        while time.time() < deadline:
            if get_sse_bus().subscriber_count(str(user_id)) > 0:
                publish_user_event(user_id, 'visit.scheduled', resource_id=resource_id)
                return
            time.sleep(0.02)

    thread = threading.Thread(target=publish_soon)
    thread.start()

    body = asyncio.run(run_stream())
    thread.join(timeout=5)
    assert not thread.is_alive()

    parsed = _parse_sse_frames(body)
    assert len(parsed) == 1
    assert parsed[0]['type'] == 'visit.scheduled'
    assert parsed[0]['resource_id'] == str(resource_id)


