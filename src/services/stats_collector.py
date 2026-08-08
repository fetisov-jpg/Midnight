import asyncio
import time
from typing import Any

from src.core.connection_manager import get_client
from src.core.registry import ConnectionConfig, get_registry
from src.repositories.check_cache_dbs import check_memcache_stats, check_redis_info
from src.repositories.check_mongo import check_mongo_info
from src.repositories.check_postgres import (
    get_active_requests,
    get_connection_summary,
    get_db_size,
    get_index_usage,
    get_most_used_tables,
    get_server_version,
    get_table_tree,
)


def _fmt_duration(seconds):
    if seconds is None:
        return None
    return f"{float(seconds):.2f} с"


def _fmt_size_bytes(size_bytes):
    if size_bytes is None:
        return None
    value = float(size_bytes)
    for unit in ("Б", "КБ", "МБ", "ГБ", "ТБ"):
        if value < 1024 or unit == "ТБ":
            return f"{value:.1f} {unit}"
        value /= 1024


def _pick(rows, columns, formatters=None):
    """Преобразует список словарей в {columns, rows} для таблицы на фронте"""
    if isinstance(rows, BaseException):
        return {"columns": columns, "rows": [], "error": str(rows)}
    formatters = formatters or {}
    out_rows = []
    for record in rows:
        row = []
        for col in columns:
            value = record.get(col)
            if isinstance(value, str):
                value = " ".join(value.split())
            fmt = formatters.get(col)
            if fmt and value is not None:
                value = fmt(value)
            row.append(value)
        out_rows.append(row)
    return {"columns": columns, "rows": out_rows}


async def _collect_postgres(client) -> dict[str, Any]:
    """Собирает статистику подключения PostgreSQL"""
    start = time.perf_counter()
    try:
        version, summary, requests, index_usage, top_tables, tree, db_size = (
            await asyncio.gather(
                get_server_version(client),
                get_connection_summary(client),
                get_active_requests(client),
                get_index_usage(client),
                get_most_used_tables(client),
                get_table_tree(client),
                get_db_size(client),
                return_exceptions=True,
            )
        )
        latency = round((time.perf_counter() - start) * 1000, 2)

        summary_data = {} if isinstance(summary, BaseException) else summary
        metrics = {
            "version": version.get("version") if isinstance(version, dict) else None,
            "client_connections": summary_data.get("total"),
            "active_queries": summary_data.get("active"),
            "db_size_bytes": (
                db_size.get("db_size_bytes") if isinstance(db_size, dict) else None
            ),
            "latency_ms": latency,
        }
        return {
            "status": "connected",
            "metrics": metrics,
            "tables": {
                "active_requests": _pick(
                    requests,
                    [
                        "pid",
                        "usename",
                        "application_name",
                        "state",
                        "duration_s",
                        "query",
                    ],
                    {"duration_s": _fmt_duration},
                ),
                "index_usage": _pick(
                    index_usage,
                    [
                        "schemaname",
                        "table_name",
                        "index_name",
                        "idx_scan",
                        "idx_tup_read",
                        "idx_tup_fetch",
                    ],
                ),
                "top_tables": _pick(
                    top_tables,
                    [
                        "schemaname",
                        "table_name",
                        "seq_scan",
                        "idx_scan",
                        "n_tup_ins",
                        "n_tup_upd",
                        "n_tup_del",
                        "n_live_tup",
                    ],
                ),
                "table_tree": _pick(
                    tree,
                    ["table_name", "column_count", "total_size_bytes", "columns"],
                    {"total_size_bytes": _fmt_size_bytes},
                ),
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
                "used_memory_bytes": metrics.get("used_memory"),
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
                "used_bytes": metrics.get("bytes"),
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
                "description": conn.description,
                "status": "error",
                "message": str(result),
                "metrics": {},
            }
        else:
            payload[conn.id] = {
                "type": conn.type,
                "name": conn.name,
                "description": conn.description,
                **result,
            }
    return payload
