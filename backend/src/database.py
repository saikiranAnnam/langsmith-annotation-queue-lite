from collections.abc import AsyncGenerator

import asyncpg

from src.config import settings

pool: asyncpg.Pool | None = None


async def get_pool() -> asyncpg.Pool:
    global pool
    if pool is None:
        pool = await asyncpg.create_pool(settings.database_url, min_size=2, max_size=10)
    return pool


async def get_connection() -> AsyncGenerator[asyncpg.Connection, None]:
    pool = await get_pool()
    async with pool.acquire() as connection:
        yield connection


async def close_pool():
    global pool
    if pool is not None:
        await pool.close()
        pool = None
