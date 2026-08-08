from src.core.database import get_pg_pool


async def check_version(pool=None):
    pool = pool or await get_pg_pool()
    async with pool.acquire() as conn:
        version = await conn.fetchval("SELECT version()")
    return {"version": version}


async def check_requests(pool=None):
    pool = pool or await get_pg_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT * FROM pg_stat_activity;")
    return request_to_dict(rows)


async def get_users(pool=None):
    pool = pool or await get_pg_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT usename, usesuper, usecreatedb, valuntil FROM pg_user;"
        )
    return request_to_dict(rows)


async def get_tables(pool=None):
    pool = pool or await get_pg_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT tablename FROM pg_tables WHERE schemaname = 'public';"
        )
    return request_to_dict(rows)


async def get_databases(pool=None):
    pool = pool or await get_pg_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT datname FROM pg_database;")
    return request_to_dict(rows)


async def get_transactions(pool=None):
    pool = pool or await get_pg_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT pid, usename, application_name, client_addr, state, query, query_start, 
                   now() - query_start AS duration 
            FROM pg_stat_activity 
            ORDER BY duration DESC;
        """)
    return request_to_dict(rows)


async def get_table_indexes(table_name: str, pool=None):
    pool = pool or await get_pg_pool()
    try:
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT indexname, indexdef
                FROM pg_indexes
                WHERE tablename = $1
                ORDER BY indexname;
            """,
                table_name,
            )
        return {"table": table_name, "indexes": request_to_dict(rows)}
    except Exception as e:
        return {"error": str(e), "table": table_name}


async def get_schema_indexes(pool=None):
    pool = pool or await get_pg_pool()
    try:
        async with pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT
                    schemaname, tablename, indexname, indexdef,
                    (SELECT array_agg(column_name) 
                     FROM information_schema.columns 
                     WHERE table_name = pg_indexes.tablename 
                       AND table_schema = pg_indexes.schemaname) AS columns
                FROM pg_indexes
                WHERE schemaname = 'public'
                ORDER BY tablename, indexname;
            """)
        return {"indexes": request_to_dict(rows)}
    except Exception as e:
        return {"error": str(e)}


async def get_extensions(pool=None):
    pool = pool or await get_pg_pool()
    try:
        async with pool.acquire() as conn:
            # Примечание: таблица pg_extensions может отсутствовать в старых версиях PG
            # Используйте pg_available_extensions если нужно
            rows = await conn.fetch("SELECT * FROM pg_available_extensions;")
        return {"extensions": request_to_dict(rows)}
    except Exception as e:
        return {"error": str(e)}


async def get_all_views(pool=None):
    pool = pool or await get_pg_pool()
    try:
        async with pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT schemaname, viewname, viewowner, definition
                FROM pg_views
                WHERE schemaname = 'public'
                ORDER BY viewname;
            """)
        return {"views": request_to_dict(rows)}
    except Exception as e:
        return {"error": str(e)}


async def get_all_materialized_views(pool=None):
    pool = pool or await get_pg_pool()
    try:
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT * FROM pg_matviews ORDER BY schemaname, matviewname;"
            )
        return {"materialized_views": request_to_dict(rows)}
    except Exception as e:
        return {"error": str(e)}


def request_to_dict(rows):
    return [dict(row) for row in rows]
