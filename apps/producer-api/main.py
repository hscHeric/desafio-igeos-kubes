import asyncio
import json
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from uuid import uuid4

import uvicorn
from aiokafka import AIOKafkaProducer
from aiokafka.admin import AIOKafkaAdminClient
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, ValidationError, field_validator
from starlette.exceptions import HTTPException as StarletteHTTPException

from config import Settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s service=producer-api level=%(levelname)s %(message)s")
log = logging.getLogger(__name__)


class MessageInput(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")
    text: str

    @field_validator("text")
    @classmethod
    def validate_text(cls, value):
        value = value.strip()
        if not 1 <= len(value) <= 1000 or "\x00" in value:
            raise ValueError("Use entre 1 e 1000 caracteres.")
        value.encode("utf-8")
        return value


@asynccontextmanager
async def lifespan(app):
    settings = app.state.settings
    producer = admin = None
    for attempt in range(1, 6):
        producer = AIOKafkaProducer(
            bootstrap_servers=settings.brokers, client_id="producer-api",
            acks="all", request_timeout_ms=5000,
        )
        admin = AIOKafkaAdminClient(bootstrap_servers=settings.brokers, request_timeout_ms=5000)
        try:
            async with asyncio.timeout(10):
                await producer.start()
                await admin.start()
            break
        except Exception as error:
            await producer.stop()
            await admin.close()
            log.warning("event=startup_retry attempt=%s error_type=%s", attempt, type(error).__name__)
            if attempt == 5:
                raise RuntimeError("Kafka indisponível após 5 tentativas; confira os logs e a configuração.") from None
            await asyncio.sleep(2)
    app.state.producer = producer
    app.state.admin = admin
    log.info("event=started")
    try:
        yield
    finally:
        await producer.stop()
        await admin.close()


def create_app():
    app = FastAPI(title="Produtor de mensagens", lifespan=lifespan)
    app.state.settings = Settings()

    @app.exception_handler(StarletteHTTPException)
    async def http_error(request, error):
        return JSONResponse({"error": str(error.detail)}, status_code=error.status_code)

    @app.exception_handler(Exception)
    async def unexpected_error(request, error):
        log.error("event=request_failed error_type=%s", type(error).__name__)
        return JSONResponse({"error": "Erro interno."}, status_code=500)

    @app.get("/health/live")
    async def live():
        return {"status": "ok", "service": "producer-api"}

    @app.get("/health/ready")
    async def ready():
        try:
            async with asyncio.timeout(5):
                topics = await app.state.admin.describe_topics([app.state.settings.topic])
                if not topics or topics[0]["error_code"] != 0:
                    raise RuntimeError("Tópico indisponível")
        except Exception:
            raise HTTPException(503, "Kafka ou tópico indisponível.") from None
        return {"status": "ready", "service": "producer-api"}

    @app.post("/messages", status_code=202)
    async def publish(request: Request):
        if request.headers.get("content-type", "").split(";")[0].strip().lower() != "application/json":
            raise HTTPException(415, "Use Content-Type: application/json.")
        body = bytearray()
        async for chunk in request.stream():
            body.extend(chunk)
            if len(body) > 16 * 1024:
                raise HTTPException(413, "Corpo acima de 16 KiB.")
        try:
            data = MessageInput.model_validate_json(bytes(body))
        except (ValidationError, UnicodeError):
            raise HTTPException(400, "Envie um JSON com text entre 1 e 1000 caracteres, sem campos adicionais.") from None
        event = {"id": str(uuid4()), "text": data.text, "createdAt": datetime.now(timezone.utc).isoformat()}
        try:
            async with asyncio.timeout(10):
                await app.state.producer.send_and_wait(
                    app.state.settings.topic,
                    json.dumps(event, ensure_ascii=False).encode("utf-8"),
                    key=event["id"].encode("ascii"),
                )
        except Exception as error:
            log.warning("event=publish_failed message_id=%s error_type=%s", event["id"], type(error).__name__)
            raise HTTPException(503, "Não foi possível confirmar a publicação. Confira o histórico antes de tentar novamente.") from None
        log.info("event=published message_id=%s", event["id"])
        return event

    return app


app = create_app()

if __name__ == "__main__":
    uvicorn.run(app, host=app.state.settings.host, port=app.state.settings.port)
