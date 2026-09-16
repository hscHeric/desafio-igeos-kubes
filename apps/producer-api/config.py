from typing import Annotated

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore",
        frozen=True, hide_input_in_errors=True,
    )

    host: str = "0.0.0.0"
    port: int = 8001
    brokers: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: ["localhost:9092"], validation_alias="KAFKA_BROKERS",
    )
    topic: str = Field(default="messages", validation_alias="KAFKA_TOPIC")

    @field_validator("brokers", mode="before")
    @classmethod
    def parse_brokers(cls, value):
        return value.split(",") if isinstance(value, str) else value
