import asyncio
from typing import Any

from src.core.connection_manager import get_client
from src.core.registry import ConnectionConfig
from src.repositories.check_cache_dbs import check_memcache_stats, check_redis_info
from src.repositories.check_mongo import (
    check_mongo_databases,
    check_mongo_db_stats,
    check_mongo_info,
)
from src.repositories.check_postgres import (
    get_active_requests,
    get_all_materialized_views,
    get_all_views,
    get_connection_summary,
    get_databases,
    get_db_size,
    get_extensions,
    get_index_usage,
    get_most_used_tables,
    get_schema_indexes,
    get_server_version,
    get_table_tree,
    get_tables,
    get_transactions,
    get_users,
)


def _fmt_gb(size_bytes):
    if size_bytes is None:
        return None
    return f"{size_bytes / (1024 ** 3):.2f} ГБ"


def _pct(part, total):
    if not total:
        return "0%"
    return f"{round(part / total * 100)}%"


def _section(title: str, data: Any) -> dict:
    if isinstance(data, dict):
        return {"title": title, "kind": "kv", "data": data}
    if isinstance(data, list):
        return {"title": title, "kind": "table", "data": data}
    return {"title": title, "kind": "kv", "data": {"value": data}}


def _error_section(title: str, message: Any) -> dict:
    return {"title": title, "kind": "error", "message": str(message)}


def _normalize(title: str, result: Any) -> dict:
    """Приводит результат репозитория к секции карточки"""
    if isinstance(result, BaseException):
        return _error_section(title, result)
    if isinstance(result, dict):
        error = result.get("error")
        if error:
            return _error_section(title, error)
        if "status" in result and result.get("status") != "connected":
            return _error_section(title, result.get("message") or "Not connected")
        # Разворачиваем обёртки вида {"key": [rows]} или {"key": {...}}
        if len(result) == 1:
            value = next(iter(result.values()))
            if isinstance(value, list):
                return _section(title, value)
            if isinstance(value, dict):
                return _section(title, value)
        return _section(title, result)
    if isinstance(result, list):
        return _section(title, result)
    return _section(title, result)


async def _pg_summary_section(pool: Any) -> dict:
    """Сводка «Объём и нагрузка» для PostgreSQL"""
    size, summary = await asyncio.gather(
        get_db_size(pool), get_connection_summary(pool), return_exceptions=True
    )
    data: dict[str, Any] = {}
    if isinstance(size, dict) and size.get("db_size_bytes"):
        data["Размер БД"] = _fmt_gb(size["db_size_bytes"])
    if isinstance(summary, dict):
        total = summary.get("total") or 0
        active = summary.get("active") or 0
        data["Подключения"] = total
        data["Активных запросов"] = active
        data["Нагрузка"] = _pct(active, total)
    return {"title": "Объём и нагрузка", "kind": "kv", "data": data}


async def _postgres_sections(pool: Any) -> list[dict]:
    summary = await _pg_summary_section(pool)
    checks = [
        ("Версия", get_server_version(pool)),
        ("Активные запросы", get_active_requests(pool)),
        ("Пользователи", get_users(pool)),
        ("Таблицы", get_tables(pool)),
        ("Базы данных", get_databases(pool)),
        ("Транзакции", get_transactions(pool)),
        ("Индексы схемы", get_schema_indexes(pool)),
        ("Частота использования индексов", get_index_usage(pool)),
        ("Самые используемые таблицы", get_most_used_tables(pool)),
        ("Дерево таблиц", get_table_tree(pool)),
        ("Расширения", get_extensions(pool)),
        ("Представления", get_all_views(pool)),
        ("Материализованные представления", get_all_materialized_views(pool)),
    ]
    titles, tasks = zip(*checks)
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return [summary] + [_normalize(t, r) for t, r in zip(titles, results)]


async def _redis_sections(client: Any) -> list[dict]:
    result = await check_redis_info(client)
    if isinstance(result, dict) and result.get("status") != "connected":
        return [_error_section("Информация", result.get("message") or "Not connected")]
    if isinstance(result, BaseException):
        return [_error_section("Информация", result)]
    info = dict(result.get("info") or {})
    if result.get("db_size") is not None:
        info["db_size"] = result["db_size"]
    data: dict[str, Any] = {}
    if info.get("used_memory_human"):
        data["Объём памяти"] = info["used_memory_human"]
    if info.get("connected_clients") is not None:
        data["Клиентов"] = info["connected_clients"]
    if result.get("db_size") is not None:
        data["Ключей"] = result["db_size"]
    summary = {"title": "Объём и нагрузка", "kind": "kv", "data": data}
    return [summary, _section("Информация", info)]


async def _memcache_sections(client: Any) -> list[dict]:
    result = await check_memcache_stats(client)
    if isinstance(result, dict) and result.get("status") != "connected":
        return [_error_section("Статистика", result.get("message") or "Not connected")]
    if isinstance(result, BaseException):
        return [_error_section("Статистика", result)]
    stats = dict(result.get("stats") or {})
    data: dict[str, Any] = {}
    if stats.get("bytes") is not None:
        data["Объём данных"] = _fmt_gb(stats["bytes"])
    if stats.get("curr_connections") is not None:
        data["Соединений"] = stats["curr_connections"]
    if stats.get("curr_items") is not None:
        data["Элементов"] = stats["curr_items"]
    summary = {"title": "Объём и нагрузка", "kind": "kv", "data": data}
    return [summary, _section("Статистика", result.get("stats") or {})]


async def _mongo_sections(client: Any, config: ConnectionConfig) -> list[dict]:
    info, databases, db_stats = await asyncio.gather(
        check_mongo_info(client, config),
        check_mongo_databases(client),
        check_mongo_db_stats(client, config),
        return_exceptions=True,
    )

    sections: list[dict] = []

    info_data = dict((info.get("info") if isinstance(info, dict) else None) or {})
    stats = dict((db_stats.get("stats") if isinstance(db_stats, dict) else None) or {})
    summary_data: dict[str, Any] = {}
    if stats.get("storage_size_bytes"):
        summary_data["Объём данных"] = _fmt_gb(stats["storage_size_bytes"])
    if info_data.get("connections") is not None:
        summary_data["Подключений"] = info_data["connections"]
    if stats.get("objects") is not None:
        summary_data["Документов"] = stats["objects"]
    if stats.get("collections") is not None:
        summary_data["Коллекций"] = stats["collections"]
    sections.append({"title": "Объём и нагрузка", "kind": "kv", "data": summary_data})

    if isinstance(info, BaseException):
        sections.append(_error_section("Сервер", info))
    elif info.get("status") != "connected":
        sections.append(
            _error_section("Сервер", info.get("message") or "Not connected")
        )
    else:
        sections.append(_section("Сервер", info.get("info") or {}))

    if isinstance(databases, BaseException):
        sections.append(_error_section("Базы данных", databases))
    elif databases.get("status") != "connected":
        sections.append(
            _error_section("Базы данных", databases.get("message") or "Not connected")
        )
    else:
        sections.append(_section("Базы данных", databases.get("databases") or []))

    if isinstance(db_stats, BaseException):
        sections.append(_error_section("Статистика БД", db_stats))
    elif db_stats.get("status") != "connected":
        sections.append(
            _error_section("Статистика БД", db_stats.get("message") or "Not connected")
        )
    else:
        stats = dict(db_stats.get("stats") or {})
        stats["database"] = db_stats.get("database")
        sections.append(_section("Статистика БД", stats))

    return sections


async def collect_connection_details(config: ConnectionConfig) -> dict:
    """Собирает детальную статистику подключения для карточки «Детали»"""
    try:
        client = await get_client(config)
    except Exception as exc:
        return {
            "id": config.id,
            "type": config.type,
            "name": config.name,
            "description": config.description,
            "status": "error",
            "message": str(exc),
            "sections": [],
        }

    if config.type == "postgres":
        sections = await _postgres_sections(client)
    elif config.type == "redis":
        sections = await _redis_sections(client)
    elif config.type == "memcache":
        sections = await _memcache_sections(client)
    elif config.type == "mongo":
        sections = await _mongo_sections(client, config)
    else:
        sections = [_error_section("Подключение", f"Unsupported type: {config.type}")]

    return {
        "id": config.id,
        "type": config.type,
        "name": config.name,
        "description": config.description,
        "status": "connected" if sections else "error",
        "sections": sections,
    }
