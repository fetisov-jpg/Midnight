import asyncio
from typing import Any

import aiomcache
import asyncpg
import redis.asyncio as aioredis
from motor.motor_asyncio import AsyncIOMotorClient

from src.core.registry import ConnectionConfig

_clients: dict[str, Any] = {}
_client_lock = asyncio.Lock()


async def get_client(config: ConnectionConfig) -> Any:
    """Возвращает клиент подключения, создавая его при первом обращении"""
    if config.id in _clients:
        return _clients[config.id]
    async with _client_lock:
        if config.id not in _clients:
            _clients[config.id] = await _create_client(config)
    return _clients[config.id]


async def _create_client(config: ConnectionConfig) -> Any:
    if config.type == "postgres":
        return await asyncpg.create_pool(
            host=config.host,
            port=config.port,
            user=config.user or "",
            password=config.password or "",
            database=config.database or "postgres",
            min_size=0,
            max_size=5,
        )
    if config.type == "redis":
        return aioredis.from_url(
            _redis_url(config),
            encoding="utf-8",
            decode_responses=True,
        )
    if config.type == "memcache":
        return aiomcache.Client(host=config.host, port=config.port)
    if config.type == "mongo":
        return AsyncIOMotorClient(_mongo_uri(config))
    raise ValueError(f"Unsupported connection type: {config.type}")


def _redis_url(config: ConnectionConfig) -> str:
    auth = f":{config.password}@{config.host}" if config.password else config.host
    db = config.database or "0"
    return f"redis://{auth}:{config.port}/{db}"


def _mongo_uri(config: ConnectionConfig) -> str:
    auth = ""
    if config.user and config.password:
        auth = f"{config.user}:{config.password}@"
    db = config.database or "admin"
    return f"mongodb://{auth}{config.host}:{config.port}/{db}"


async def close_client(connection_id: str) -> None:
    client = _clients.pop(connection_id, None)
    if client is None:
        return
    if isinstance(client, (asyncpg.Pool, aioredis.Redis, aiomcache.Client)):
        await client.close()
    elif isinstance(client, AsyncIOMotorClient):
        client.close()


async def close_all_clients() -> None:
    for connection_id in list(_clients):
        await close_client(connection_id)
