import asyncio
import time
from typing import Any

from src.core.connection_manager import get_client
from src.core.registry import ConnectionConfig, get_registry
from src.repositories.check_cache_dbs import check_memcache_stats, check_redis_info
from src.repositories.check_mongo import check_mongo_info
from src.repositories.check_postgres import check_requests, check_version


async def _collect_postgres(client) -> dict[str, Any]:
    """Собирает статистику подключения PostgreSQL"""
    start = time.perf_counter()
    try:
        version = await check_version(client)
        requests = await check_requests(client)
        requests = requests if isinstance(requests, list) else []
        latency = round((time.perf_counter() - start) * 1000, 2)
        return {
            "status": "connected",
            "metrics": {
                "version": version.get("version"),
                "active_connections": len(requests),
                "latency_ms": latency,
            },
        }
    except Exception as exc:
        latency = round((time.perf_counter() - start) * 1000, 2)
        return {
            "status": "error",
            "message": str(exc),
            "metrics": {"latency_ms": latency},
        }


async def _collect_redis(client) -> dict[str, Any]:
    """Собирает статистику подключения Redis"""
    start = time.perf_counter()
    try:
        info = await check_redis_info(client)
        latency = round((time.perf_counter() - start) * 1000, 2)
        if info.get("status") != "connected":
            return {
                "status": "error",
                "message": info.get("message"),
                "metrics": {"latency_ms": latency},
            }

        metrics = info.get("info", {})
        return {
            "status": "connected",
            "metrics": {
                "version": metrics.get("redis_version"),
                "uptime_seconds": metrics.get("uptime_in_seconds"),
                "used_memory_human": metrics.get("used_memory_human"),
                "connected_clients": metrics.get("connected_clients"),
                "db_size": info.get("db_size"),
                "latency_ms": latency,
            },
        }
    except Exception as exc:
        latency = round((time.perf_counter() - start) * 1000, 2)
        return {
            "status": "error",
            "message": str(exc),
            "metrics": {"latency_ms": latency},
        }


async def _collect_memcache(client) -> dict[str, Any]:
    """Собирает статистику подключения Memcached"""
    start = time.perf_counter()
    try:
        info = await check_memcache_stats(client)
        latency = round((time.perf_counter() - start) * 1000, 2)
        if info.get("status") != "connected":
            return {
                "status": "error",
                "message": info.get("message"),
                "metrics": {"latency_ms": latency},
            }

        metrics = info.get("stats", {})
        return {
            "status": "connected",
            "metrics": {
                "uptime": metrics.get("uptime"),
                "curr_items": metrics.get("curr_items"),
                "total_items": metrics.get("total_items"),
                "curr_connections": metrics.get("curr_connections"),
                "get_hits": metrics.get("get_hits"),
                "get_misses": metrics.get("get_misses"),
                "latency_ms": latency,
            },
        }
    except Exception as exc:
        latency = round((time.perf_counter() - start) * 1000, 2)
        return {
            "status": "error",
            "message": str(exc),
            "metrics": {"latency_ms": latency},
        }


async def _collect_mongo(client) -> dict[str, Any]:
    """Собирает статистику подключения MongoDB"""
    start = time.perf_counter()
    try:
        info = await check_mongo_info(client)
        latency = round((time.perf_counter() - start) * 1000, 2)
        if info.get("status") != "connected":
            return {
                "status": "error",
                "message": info.get("message"),
                "metrics": {"latency_ms": latency},
            }

        metrics = info.get("info", {})
        return {
            "status": "connected",
            "metrics": {
                "version": metrics.get("version"),
                "uptime_seconds": metrics.get("uptime_in_seconds"),
                "connections": metrics.get("connections"),
                "latency_ms": latency,
            },
        }
    except Exception as exc:
        latency = round((time.perf_counter() - start) * 1000, 2)
        return {
            "status": "error",
            "message": str(exc),
            "metrics": {"latency_ms": latency},
        }


async def collect_connection_stats(config: ConnectionConfig) -> dict[str, Any]:
    """Собирает статистику одного подключения"""
    try:
        client = await get_client(config)
    except Exception as exc:
        return {"status": "error", "message": str(exc), "metrics": {}}

    if config.type == "postgres":
        return await _collect_postgres(client)
    if config.type == "redis":
        return await _collect_redis(client)
    if config.type == "memcache":
        return await _collect_memcache(client)
    if config.type == "mongo":
        return await _collect_mongo(client)
    return {
        "status": "error",
        "message": f"Unsupported type: {config.type}",
        "metrics": {},
    }


async def collect_all_stats() -> dict[str, Any]:
    """Собирает статистику всех подключений параллельно"""
    connections = get_registry().list()
    results = await asyncio.gather(
        *(collect_connection_stats(c) for c in connections),
        return_exceptions=True,
    )

    payload: dict[str, Any] = {}
    for conn, result in zip(connections, results):
        if isinstance(result, BaseException):
            payload[conn.id] = {
                "type": conn.type,
                "name": conn.name,
                "status": "error",
                "message": str(result),
                "metrics": {},
            }
        else:
            payload[conn.id] = {"type": conn.type, "name": conn.name, **result}
    return payload
