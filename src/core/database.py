import os
from typing import Optional

import asyncpg
from dotenv import load_dotenv

from src.core.config import PostgresConfig

load_dotenv()

_pg_pool: Optional[asyncpg.Pool] = None


def _build_pg_pool_kwargs() -> dict:
    cfg = PostgresConfig.from_env()
    return dict(
        host=cfg.host,
        port=cfg.port,
        user=cfg.user,
        password=cfg.password,
        database=cfg.database,
        min_size=1,
        max_size=5,
    )


async def get_pg_pool() -> asyncpg.Pool:
    global _pg_pool
    if _pg_pool is None:
        _pg_pool = await asyncpg.create_pool(**_build_pg_pool_kwargs())
    return _pg_pool


async def close_pg() -> None:
    global _pg_pool
    if _pg_pool is not None:
        await _pg_pool.close()
        _pg_pool = None
