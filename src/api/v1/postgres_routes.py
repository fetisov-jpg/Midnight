from fastapi import APIRouter, HTTPException
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
    get_all_materialized_views
)
from src.core.database import get_postgres_config

router = APIRouter(prefix="/postgres", tags=["postgres"])


@router.get("/")
def root():
    return {"message": "PostgreSQL endpoints"}


@router.get("/ping")
async def ping():
    return {"status": "pong"}


@router.get("/config")
async def get_config():
    """Возвращает текущую конфигурацию PostgreSQL"""
    config = get_postgres_config()
    return {
        "host": config.host,
        "port": config.port,
        "user": config.user,
        "database": config.database,
    }


@router.get("/db-test")
async def test_db():
    """Проверяет подключение к базе данных"""
    try:
        from src.core.database import get_db_conn
        conn = await get_db_conn()
        await conn.close()
        return {"status": "ok", "message": "Database connected"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.get("/check-version")
async def check_version_pg():
    return await check_version()


@router.get("/requests")
async def check_requests_pg():
    try:
        return await check_requests()
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.get("/users")
async def get_users_count():
    try:
        return await get_users()
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.get("/tables")
async def get_tables_pg():
    try:
        return await get_tables()
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.get("/databases")
async def get_database_pg():
    try:
        return await get_databases()
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.get("/transactions")
async def get_transactions_pg():
    try:
        return await get_transactions()
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.get("/indexes/{table_name}")
async def get_table_indexes_(table: str):
    return await get_table_indexes(table_name=table)


@router.get("/indexes")
async def get_schema_indexes_pg():
    try:
        return await get_schema_indexes()
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.get("/extensions")
async def get_extensions_pg():
    try:
        return await get_extensions()
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.get("/views")
async def get_all_views_pg():
    try:
        return await get_all_views()
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.get("/materialized_views")
async def get_all_materialized_views_pg():
    try:
        return await get_all_materialized_views()
    except Exception as e:
        return {"status": "error", "message": str(e)}
