from fastapi import APIRouter, HTTPException

from src.core.config import get_postgres_config
from src.core.database import get_pg_pool
from src.repositories.check_postgres import (
    check_version,
    check_requests,
    get_users,
    get_tables,
    get_databases,
    get_transactions,
    get_table_indexes,
    get_schema_indexes,
    get_extensions,
    get_all_views,
    get_all_materialized_views,
)

router = APIRouter(prefix="/postgres", tags=["postgres"])


@router.get("/")
def root() -> dict:
    return {"message": "PostgreSQL endpoints"}


@router.get("/ping")
async def ping() -> dict:
    return {"status": "pong"}


@router.get("/config")
async def get_config() -> dict:
    config = get_postgres_config()
    return {
        "host": config.host,
        "port": config.port,
        "user": config.user,
        "database": config.database,
    }


@router.get("/db-test")
async def test_db() -> dict:
    try:
        pool = await get_pg_pool()
        async with pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
        return {"status": "ok", "message": "Database connected"}
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


@router.get("/check-version")
async def check_version_pg() -> dict:
    return await check_version()


@router.get("/requests")
async def check_requests_pg() -> dict:
    try:
        return await check_requests()
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


@router.get("/users")
async def get_users_pg() -> dict:
    try:
        return await get_users()
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


@router.get("/tables")
async def get_tables_pg() -> dict:
    try:
        return await get_tables()
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


@router.get("/databases")
async def get_database_pg() -> dict:
    try:
        return await get_databases()
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


@router.get("/transactions")
async def get_transactions_pg() -> dict:
    try:
        return await get_transactions()
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


@router.get("/indexes/{table_name}")
async def get_table_indexes_endpoint(table_name: str) -> dict:
    return await get_table_indexes(table_name=table_name)


@router.get("/indexes")
async def get_schema_indexes_pg() -> dict:
    try:
        return await get_schema_indexes()
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


@router.get("/extensions")
async def get_extensions_pg() -> dict:
    try:
        return await get_extensions()
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


@router.get("/views")
async def get_all_views_pg() -> dict:
    try:
        return await get_all_views()
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


@router.get("/materialized_views")
async def get_all_materialized_views_pg() -> dict:
    try:
        return await get_all_materialized_views()
    except Exception as exc:
        return {"status": "error", "message": str(exc)}
