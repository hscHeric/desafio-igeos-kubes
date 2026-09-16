import asyncio
import logging
from contextlib import asynccontextmanager, suppress
from uuid import UUID

import asyncpg
import uvicorn
from aiokafka import AIOKafkaConsumer, TopicPartition
from aiokafka.admin import AIOKafkaAdminClient
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, field_validator
from starlette.exceptions import HTTPException as StarletteHTTPException

from config import Settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s service=consumer-api level=%(levelname)s %(message)s")
log = logging.getLogger(__name__)


class Event(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: UUID
    text: str = Field(strict=True, min_length=1, max_length=1000)
    createdAt: AwareDatetime

    @field_validator("text")
    @classmethod
    def valid_text(cls, value):
        if value != value.strip() or "\x00" in value:
            raise ValueError("Texto deve estar normalizado.")
        value.encode("utf-8")
        return value


async def consume(app):
    consumer, pool = app.state.consumer, app.state.pool
    try:
        while True:
            record = await consumer.getone()
            event = Event.model_validate_json(record.value)
            if record.key != str(event.id).encode("ascii"):
                raise ValueError("Chave Kafka diferente do identificador do evento")
            # Uma instrução em autocommit: ao retornar, a gravação já é durável.
            # Em caso de falha não avançamos o offset; reiniciar permite releitura.
            await pool.execute(
                "INSERT INTO messages(id, text, created_at) VALUES($1, $2, $3) ON CONFLICT (id) DO NOTHING",
                event.id, event.text, event.createdAt,
            )
            await consumer.commit({TopicPartition(record.topic, record.partition): record.offset + 1})
            log.info("event=persisted message_id=%s partition=%s offset=%s", event.id, record.partition, record.offset)
    except Exception as error:
        log.error("event=consumer_stopped error_type=%s action=restart_after_fix", type(error).__name__)


@asynccontextmanager
async def lifespan(app):
    settings = app.state.settings
    consumer = admin = pool = None
    for attempt in range(1, 6):
        consumer = AIOKafkaConsumer(
            settings.topic, bootstrap_servers=settings.brokers, group_id=settings.group_id,
            client_id="consumer-api", enable_auto_commit=False, auto_offset_reset="earliest",
            request_timeout_ms=10000,
        )
        admin = AIOKafkaAdminClient(bootstrap_servers=settings.brokers, request_timeout_ms=5000)
        try:
            async with asyncio.timeout(15):
                pool = await asyncpg.create_pool(settings.database_url, min_size=1, max_size=5, timeout=5, command_timeout=5)
                await pool.fetchval("SELECT 1 FROM messages LIMIT 1")
                await admin.start()
                await consumer.start()
            break
        except Exception as error:
            await consumer.stop()
            await admin.close()
            if pool is not None:
                pool.terminate()
                pool = None
            log.warning("event=startup_retry attempt=%s error_type=%s", attempt, type(error).__name__)
            if attempt == 5:
                raise RuntimeError("Dependências indisponíveis após 5 tentativas; confira configuração e preparação.") from None
            await asyncio.sleep(2)
    app.state.consumer, app.state.admin, app.state.pool = consumer, admin, pool
    task = asyncio.create_task(consume(app))
    app.state.worker = task
    log.info("event=started")
    try:
        yield
    finally:
        task.cancel()
        with suppress(asyncio.CancelledError):
            await task
        await consumer.stop()
        await admin.close()
        try:
            async with asyncio.timeout(5):
                await pool.close()
        except TimeoutError:
            pool.terminate()


def create_app():
    app = FastAPI(title="Consumidor de mensagens", lifespan=lifespan)
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
        return {"status": "ok", "service": "consumer-api"}

    @app.get("/health/ready")
    async def ready():
        try:
            if app.state.worker.done():
                raise RuntimeError("Consumidor parado")
            async with asyncio.timeout(5):
                await app.state.pool.fetchval("SELECT 1")
                topics = await app.state.admin.describe_topics([app.state.settings.topic])
                if not topics or topics[0]["error_code"] != 0:
                    raise RuntimeError("Tópico indisponível")
        except Exception:
            raise HTTPException(503, "Kafka, PostgreSQL ou consumidor indisponível.") from None
        return {"status": "ready", "service": "consumer-api"}

    @app.get("/messages")
    async def messages():
        try:
            rows = await app.state.pool.fetch(
                "SELECT id, text, created_at, processed_at FROM messages ORDER BY processed_at DESC, id DESC LIMIT 100"
            )
        except Exception as error:
            log.warning("event=query_failed error_type=%s", type(error).__name__)
            raise HTTPException(503, "Não foi possível consultar o histórico.") from None
        return {"messages": [
            {"id": str(row["id"]), "text": row["text"], "createdAt": row["created_at"].isoformat(), "processedAt": row["processed_at"].isoformat()}
            for row in rows
        ]}

    return app


app = create_app()

if __name__ == "__main__":
    uvicorn.run(app, host=app.state.settings.host, port=app.state.settings.port)
