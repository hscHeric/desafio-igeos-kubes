"""Teste opcional com banco real; usa e remove somente um schema exclusivo."""
import asyncio
import os
from pathlib import Path
from uuid import uuid4

import asyncpg
import httpx
import pytest

from main import create_app


@pytest.mark.skipif(not os.getenv("TEST_DATABASE_URL"), reason="TEST_DATABASE_URL não definido")
def test_database_uniqueness_and_history_limit():
    async def scenario():
        schema = "test_" + uuid4().hex
        conn = await asyncpg.connect(os.environ["TEST_DATABASE_URL"])
        pool = None
        try:
            await conn.execute(f'CREATE SCHEMA "{schema}"')
            pool = await asyncpg.create_pool(os.environ["TEST_DATABASE_URL"], min_size=1, max_size=2, server_settings={"search_path": schema})
            await pool.execute(Path("schema.sql").read_text(encoding="utf-8"))
            message_id = uuid4()
            sql = "INSERT INTO messages(id,text,created_at) VALUES($1,$2,now()) ON CONFLICT (id) DO NOTHING"
            await pool.execute(sql, message_id, "original")
            before = await pool.fetchrow("SELECT * FROM messages WHERE id=$1", message_id)
            await pool.execute(sql, message_id, "repetido")
            assert await pool.fetchrow("SELECT * FROM messages WHERE id=$1", message_id) == before
            for _ in range(105):
                await pool.execute(sql, uuid4(), "mesmo texto")
            assert await pool.fetchval("SELECT count(*) FROM messages") == 106
            app = create_app()
            app.state.pool = pool
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app), base_url="http://test") as client:
                rows = (await client.get("/messages")).json()["messages"]
            assert len(rows) == 100
            assert rows == sorted(rows, key=lambda row: (row["processedAt"], row["id"]), reverse=True)
        finally:
            if pool is not None:
                await pool.close()
            await conn.execute(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE')
            await conn.close()

    asyncio.run(scenario())
