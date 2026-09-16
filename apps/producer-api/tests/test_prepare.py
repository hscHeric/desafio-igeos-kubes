import asyncio
from unittest.mock import AsyncMock, Mock

import pytest

import prepare


@pytest.mark.parametrize("error_code", [0, 36])
def test_create_or_existing_topic_succeeds(monkeypatch, error_code):
    admin = AsyncMock()
    response = Mock()
    response.to_object.return_value = {"topic_errors": [{"topic": "messages", "error_code": error_code}]}
    admin.create_topics.return_value = response
    monkeypatch.setattr(prepare, "AIOKafkaAdminClient", lambda **kwargs: admin)
    asyncio.run(prepare.prepare())
    admin.close.assert_awaited_once()


def test_broker_rejection_is_not_reported_as_success(monkeypatch):
    admin = AsyncMock()
    response = Mock()
    response.to_object.return_value = {"topic_errors": [{"topic": "messages", "error_code": 29}]}
    admin.create_topics.return_value = response
    monkeypatch.setattr(prepare, "AIOKafkaAdminClient", lambda **kwargs: admin)
    monkeypatch.setattr(prepare.asyncio, "sleep", AsyncMock())
    with pytest.raises(SystemExit, match="Não foi possível"):
        asyncio.run(prepare.prepare())
    assert admin.create_topics.await_count == 5
