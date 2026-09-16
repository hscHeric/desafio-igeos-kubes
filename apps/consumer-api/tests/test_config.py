import pytest
from pydantic import ValidationError

from config import Settings


@pytest.fixture(autouse=True)
def isolated_environment(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    for key in ("HOST", "PORT", "KAFKA_BROKERS", "KAFKA_TOPIC", "KAFKA_GROUP_ID", "DATABASE_URL"):
        monkeypatch.delenv(key, raising=False)


def test_defaults_with_required_database(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:test-secret@db/messages")
    settings = Settings()
    assert (settings.host, settings.port, settings.brokers, settings.topic, settings.group_id) == (
        "0.0.0.0", 8002, ["localhost:9092"], "messages", "message-store",
    )
    assert "test-secret" not in repr(settings)


def test_dotenv_and_environment_keep_deploy_names(monkeypatch, tmp_path):
    (tmp_path / ".env").write_text(
        "PORT=8102\nDATABASE_URL=postgresql://user:file@db/messages\n"
        "KAFKA_BROKERS=kafka:9092,other:9092\nKAFKA_TOPIC=mensagens\nKAFKA_GROUP_ID=store\nUNRELATED_KEY=ignored\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:process@db/messages")
    settings = Settings()
    assert settings.port == 8102
    assert settings.brokers == ["kafka:9092", "other:9092"]
    assert settings.topic == "mensagens"
    assert settings.group_id == "store"
    assert settings.database_url == "postgresql://user:process@db/messages"


@pytest.mark.parametrize("database_url", [None, ""])
def test_missing_or_empty_database_is_rejected(monkeypatch, database_url):
    if database_url is not None:
        monkeypatch.setenv("DATABASE_URL", database_url)
    with pytest.raises(ValidationError):
        Settings()


def test_configuration_error_does_not_print_database_credentials(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:test-secret@db/messages")
    monkeypatch.setenv("PORT", "invalid")
    with pytest.raises(ValidationError) as error:
        Settings()
    assert "test-secret" not in str(error.value)
