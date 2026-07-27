from fastapi import APIRouter, Depends, HTTPException, Query, status

from src.core.database import get_db_conn
from src.repositories.check_postgres import (
    check_version,
    check_requests,
    get_users,
    get_tables,
    get_databases,
    get_transactions,
    get_table_indexes,
    get_schema_indexes
)

router = APIRouter(
    prefix="/postgres",  # ← Изменено с "/v1/postgres" на "/postgres"
    tags=["postgres"]
)

@router.get("/")
def root():
    return {"Hello": "World"}

@router.get("/ping")
def ping():
    return {"status": "pong"}

@router.get("/db-test")
async def test_db():
    try:
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
@router.get("/table/{table_name}")
async def get_table_endpoint(
        table_name: str,
        limit: int = Query(100, ge=1, le=1000, description="Количество записей")
):
    try:
        return await get_table_data(table_name, limit)
    except Exception as e:
        return {"status": "error", "message": str(e)}
async def get_table_data(table_name: str, limit: int = 100):
    """Получает данные из указанной таблицы"""
    conn = await get_db_conn()
    try:
        # Получаем данные
        rows = await conn.fetch(f"SELECT * FROM {table_name} LIMIT {limit}")
        return {"table": table_name, "data": [dict(row) for row in rows]}
    except Exception as e:
        return {"error": str(e), "table": table_name, "data": []}
    finally:
        await conn.close()

@router.get("/indexes/{table_name}")
async def get_table_indexes_(table :str):
   return get_table_indexes(table_name=table)

@router.get("/indexes")
async def get_schema_indexes_pg():
    try:
        return await get_schema_indexes()
    except Exception as e:
        return {"status": "error", "message": str(e)}