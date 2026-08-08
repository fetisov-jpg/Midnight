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
                   clock_timestamp() - query_start AS duration 
            FROM pg_stat_activity 
            WHERE application_name <> 'midnight-monitor'
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


async def get_server_version(pool=None):
    """Короткая версия сервера (например: 17.10)"""
    pool = pool or await get_pg_pool()
    async with pool.acquire() as conn:
        version = await conn.fetchval(
            "SELECT setting FROM pg_settings WHERE name = 'server_version'"
        )
    return {"version": version}


async def get_connection_summary(pool=None):
    """Количество клиентских подключений по состояниям (без фоновых процессов)"""
    pool = pool or await get_pg_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("""
            SELECT count(*) AS total,
                   count(*) FILTER (WHERE state = 'active') AS active,
                   count(*) FILTER (WHERE state = 'idle') AS idle
            FROM pg_stat_activity
            WHERE backend_type = 'client backend'
              AND application_name <> 'midnight-monitor';
            """)
    return dict(row)


async def get_active_requests(pool=None):
    """Активные запросы клиентских подключений (не idle)"""
    pool = pool or await get_pg_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT pid, usename, application_name, state,
                   round(extract(epoch FROM (clock_timestamp() - query_start))::numeric, 2) AS duration_s,
                   left(query, 150) AS query
            FROM pg_stat_activity
            WHERE backend_type = 'client backend'
              AND state <> 'idle'
              AND application_name <> 'midnight-monitor'
            ORDER BY duration_s DESC
            LIMIT 25;
            """)
    return request_to_dict(rows)


async def get_index_usage(pool=None):
    """Частота использования индексов (по pg_stat_user_indexes)"""
    pool = pool or await get_pg_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT schemaname, relname AS table_name, indexrelname AS index_name,
                   idx_scan, idx_tup_read, idx_tup_fetch
            FROM pg_stat_user_indexes
            ORDER BY idx_scan DESC
            LIMIT 25;
            """)
    return request_to_dict(rows)


async def get_most_used_tables(pool=None):
    """Самые используемые таблицы (по pg_stat_user_tables)"""
    pool = pool or await get_pg_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT schemaname, relname AS table_name,
                   seq_scan, idx_scan, n_tup_ins, n_tup_upd, n_tup_del, n_live_tup
            FROM pg_stat_user_tables
            ORDER BY (seq_scan + idx_scan) DESC
            LIMIT 25;
            """)
    return request_to_dict(rows)


async def get_db_size(pool=None):
    """Размер текущей базы данных в байтах"""
    pool = pool or await get_pg_pool()
    async with pool.acquire() as conn:
        size = await conn.fetchval("SELECT pg_database_size(current_database())")
    return {"db_size_bytes": int(size)}


async def get_table_tree(pool=None):
    """Дерево таблиц: таблица, число и список колонок, размер"""
    pool = pool or await get_pg_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT c.relname AS table_name,
                   (SELECT count(*) FROM pg_attribute a
                    WHERE a.attrelid = c.oid AND a.attnum > 0 AND NOT a.attisdropped) AS column_count,
                   pg_total_relation_size(c.oid) AS total_size_bytes,
                   (SELECT string_agg(a2.attname, ', ' ORDER BY a2.attnum)
                    FROM pg_attribute a2
                    WHERE a2.attrelid = c.oid AND a2.attnum > 0 AND NOT a2.attisdropped) AS columns
            FROM pg_class c
            JOIN pg_namespace n ON n.oid = c.relnamespace
            WHERE c.relkind IN ('r', 'p', 'f') AND n.nspname = 'public'
            ORDER BY c.relname
            LIMIT 100;
            """)
    return request_to_dict(rows)


def request_to_dict(rows):
    return [dict(row) for row in rows]
