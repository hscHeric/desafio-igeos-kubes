import asyncio
import json
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from main import consume, create_app


@pytest.fixture
def client():
    app = create_app()
    app.state.pool = AsyncMock()
    app.state.pool.fetch.return_value = []
    app.state.admin = AsyncMock()
    app.state.admin.describe_topics.return_value = [{"error_code": 0}]
    app.state.worker = Mock()
    app.state.worker.done.return_value = False
    return TestClient(app, raise_server_exceptions=False)


def test_history_contract(client):
    message_id = uuid4()
    now = datetime.now(timezone.utc)
    client.app.state.pool.fetch.return_value = [{"id": message_id, "text": "<script>texto</script>", "created_at": now, "processed_at": now}]
    result = client.get("/messages")
    assert result.status_code == 200
    assert result.json() == {"messages": [{"id": str(message_id), "text": "<script>texto</script>", "createdAt": now.isoformat(), "processedAt": now.isoformat()}]}


def test_query_failure_is_public_error(client):
    client.app.state.pool.fetch.side_effect = RuntimeError("password=secret")
    result = client.get("/messages")
    assert result.status_code == 503
    assert "secret" not in result.text


def test_readiness_checks_worker_and_dependencies(client):
    assert client.get("/health/ready").status_code == 200
    client.app.state.worker.done.return_value = True
    assert client.get("/health/ready").status_code == 503
    assert client.get("/health/live").status_code == 200
    client.app.state.worker.done.return_value = False
    client.app.state.pool.fetchval.side_effect = RuntimeError()
    assert client.get("/health/ready").status_code == 503


def test_metrics_endpoint_exposes_consumer_metrics(client):
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "consumer_http_requests_total" in response.text


def record():
    event = {"id": str(uuid4()), "text": "Mensagem", "createdAt": datetime.now(timezone.utc).isoformat()}
    return SimpleNamespace(topic="messages", partition=0, offset=4, key=event["id"].encode(), value=json.dumps(event).encode())


def test_commit_follows_successful_database_write():
    async def scenario():
        app = create_app()
        app.state.consumer = AsyncMock()
        app.state.pool = AsyncMock()
        event = record()
        app.state.consumer.getone.side_effect = [event, asyncio.CancelledError()]
        calls = []

        async def write(*args):
            calls.append("persisted")

        async def commit(offsets):
            assert calls == ["persisted"]
            assert list(offsets.values()) == [5]
            calls.append("committed")

        app.state.pool.execute.side_effect = write
        app.state.consumer.commit.side_effect = commit
        with pytest.raises(asyncio.CancelledError):
            await consume(app)
        assert calls == ["persisted", "committed"]

    asyncio.run(scenario())


@pytest.mark.parametrize("failure", ["database", "invalid_event", "wrong_key"])
def test_failure_never_confirms_offset(failure):
    async def scenario():
        app = create_app()
        app.state.consumer = AsyncMock()
        app.state.pool = AsyncMock()
        event = record()
        if failure == "database":
            app.state.pool.execute.side_effect = RuntimeError("secret")
        elif failure == "invalid_event":
            event.value = b'{}'
        else:
            event.key = b"different"
        app.state.consumer.getone.return_value = event
        worker = asyncio.create_task(consume(app))
        await worker
        assert worker.done()
        app.state.consumer.commit.assert_not_called()
        if failure != "database":
            app.state.pool.execute.assert_not_called()

    asyncio.run(scenario())
