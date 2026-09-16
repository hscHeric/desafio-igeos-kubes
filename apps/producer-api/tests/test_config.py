import os

import pytest
from pydantic import ValidationError

from config import Settings


@pytest.fixture(autouse=True)
def isolated_environment(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    for key in ("HOST", "PORT", "KAFKA_BROKERS", "KAFKA_TOPIC"):
        monkeypatch.delenv(key, raising=False)


def test_defaults():
    settings = Settings()
    assert (settings.host, settings.port, settings.brokers, settings.topic) == (
        "0.0.0.0", 8001, ["localhost:9092"], "messages",
    )


def test_dotenv_and_process_environment_precedence(monkeypatch, tmp_path):
    (tmp_path / ".env").write_text(
        "PORT=8101\nKAFKA_BROKERS=kafka:9092,other:9092\nKAFKA_TOPIC=mensagens\nUNRELATED_KEY=ignored\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("PORT", "8201")
    settings = Settings()
    assert settings.port == 8201
    assert settings.brokers == ["kafka:9092", "other:9092"]
    assert settings.topic == "mensagens"
    assert "KAFKA_TOPIC" not in os.environ


def test_invalid_port_is_rejected(monkeypatch):
    monkeypatch.setenv("PORT", "not-a-port")
    with pytest.raises(ValidationError):
        Settings()
