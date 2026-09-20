import asyncio
import json
from unittest.mock import AsyncMock
from uuid import UUID

import httpx
import pytest
from fastapi.testclient import TestClient

from main import create_app


@pytest.fixture
def client():
    app = create_app()
    app.state.producer = AsyncMock()
    app.state.admin = AsyncMock()
    app.state.admin.describe_topics.return_value = [{"error_code": 0}]
    return TestClient(app, raise_server_exceptions=False)


def test_publish_preserves_identity_and_normalizes_text(client):
    response = client.post("/messages", json={"text": "  Olá 🌍  "})
    assert response.status_code == 202
    event = response.json()
    UUID(event["id"])
    assert event["text"] == "Olá 🌍"
    call = client.app.state.producer.send_and_wait.call_args
    assert json.loads(call.args[1]) == event
    assert call.kwargs["key"] == event["id"].encode()


@pytest.mark.parametrize("body", [{"text": " "}, {"text": "x" * 1001}, {"text": "nul\x00"}, {"text": 123}, {}, {"text": "ok", "extra": True}])
def test_invalid_payload_does_not_publish(client, body):
    assert client.post("/messages", json=body).status_code == 400
    client.app.state.producer.send_and_wait.assert_not_called()


def test_unicode_limit_counts_codepoints(client):
    assert client.post("/messages", json={"text": "🌍" * 1000}).status_code == 202
    assert client.post("/messages", json={"text": "🌍" * 1001}).status_code == 400


def test_protocol_errors(client):
    assert client.post("/messages", content="text").status_code == 415
    assert client.post("/messages", content="{", headers={"Content-Type": "application/json"}).status_code == 400
    assert client.post("/messages", content="x" * 16385, headers={"Content-Type": "application/json"}).status_code == 413
    assert client.get("/missing").json() == {"error": "Not Found"}
    client.app.state.producer.send_and_wait.assert_not_called()


def test_failed_publish_is_not_success_and_hides_internal_error(client):
    client.app.state.producer.send_and_wait.side_effect = RuntimeError("internal-secret")
    response = client.post("/messages", json={"text": "teste"})
    assert response.status_code == 503
    assert "internal-secret" not in response.text
    assert "error" in response.json()


def test_liveness_and_readiness_are_different(client):
    assert client.get("/health/ready").status_code == 200
    client.app.state.admin.describe_topics.side_effect = RuntimeError()
    assert client.get("/health/ready").status_code == 503
    assert client.get("/health/live").status_code == 200


def test_metrics_endpoint_exposes_producer_metrics(client):
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "producer_http_requests_total" in response.text


def test_response_waits_for_kafka_acknowledgement():
    async def scenario():
        app = create_app()
        started, acknowledged = asyncio.Event(), asyncio.Event()

        async def send(*args, **kwargs):
            started.set()
            await acknowledged.wait()

        app.state.producer = AsyncMock()
        app.state.producer.send_and_wait.side_effect = send
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app), base_url="http://test") as client:
            request = asyncio.create_task(client.post("/messages", json={"text": "espera"}))
            await asyncio.wait_for(started.wait(), 2)
            assert not request.done()
            acknowledged.set()
            assert (await request).status_code == 202

    asyncio.run(scenario())
