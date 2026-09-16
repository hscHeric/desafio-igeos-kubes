"""Cria tabela e índice de forma idempotente, sem apagar registros."""
import asyncio
from pathlib import Path

import asyncpg

from config import Settings


async def prepare():
    settings = Settings()
    for attempt in range(1, 6):
        connection = None
        try:
            async with asyncio.timeout(10):
                connection = await asyncpg.connect(settings.database_url, timeout=5)
                await connection.execute(Path(__file__).with_name("schema.sql").read_text(encoding="utf-8"))
            print("Tabela messages pronta.")
            return
        except Exception as error:
            print(f"Preparação PostgreSQL: tentativa {attempt}/5; {type(error).__name__}")
            if attempt == 5:
                raise SystemExit("Não foi possível preparar o banco.") from None
            await asyncio.sleep(2)
        finally:
            if connection is not None:
                await connection.close(timeout=5)


if __name__ == "__main__":
    asyncio.run(prepare())
