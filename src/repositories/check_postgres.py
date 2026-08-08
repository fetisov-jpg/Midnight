from src.core.database import get_db_conn_pg

async def check_version():
    conn = await get_db_conn_pg()
    version = await conn.fetchval("SELECT version()")
    await conn.close()
    return {"version": version}

async def check_requests():
    conn = await get_db_conn_pg()
    rows = await conn.fetch("SELECT * FROM pg_stat_activity;")
    await conn.close()
    result =  request_to_dict(rows)
    return result

async def get_users():
    conn = await  get_db_conn_pg()
    rows = await  conn.fetch("SELECT usename, usesuper, usecreatedb, valuntil FROM pg_user;" )
    await conn.close()
    result = request_to_dict(rows)
    return result

async def get_tables():
    conn = await get_db_conn_pg()
    rows = await conn.fetch("SELECT tablename FROM pg_tables WHERE schemaname = 'public';")
    await conn.close()
    result = request_to_dict(rows)
    return result
async def get_databases():
    conn = await get_db_conn_pg()
    rows = await conn.fetch("SELECT datname FROM pg_database;")
    await conn.close()
    result = request_to_dict(rows)
    return result

async def get_transactions():
    conn = await get_db_conn_pg()
    rows = await conn.fetch("SELECT pid,usename, application_name,client_addr,state,query, query_start, now() - query_start AS duration FROM pg_stat_activity ORDER BY duration DESC;")
    await conn.close()
    result = request_to_dict(rows)
    return result

async def get_table_indexes(table_name: str):
    conn = await get_db_conn_pg()
    try:
        rows = await conn.fetch("""
            SELECT
                indexname,
                indexdef
            FROM
                pg_indexes
            WHERE
                tablename = $1
            ORDER BY
                indexname;
        """, table_name)
        return {"table": table_name, "indexes": request_to_dict(rows=rows)}
    except Exception as e:
        return {"error": str(e), "table": table_name}
    finally:
        await conn.close()

async def get_schema_indexes():
    conn = await get_db_conn_pg()
    try:
        rows = await conn.fetch("""
            SELECT
                schemaname,
                tablename,
                indexname,
                indexdef,
                (SELECT array_agg(column_name) 
                 FROM information_schema.columns 
                 WHERE table_name = pg_indexes.tablename 
                   AND table_schema = pg_indexes.schemaname) AS columns
            FROM
                pg_indexes
            WHERE
                schemaname = 'public'
            ORDER BY
                tablename,
                indexname;
        """)
        return {"indexes": request_to_dict(rows)}
    except Exception as e:
        return {"error": str(e)}
    finally:
        await conn.close()

async def get_extensions():
    conn = await get_db_conn_pg()
    try:
        rows = await conn.fetch("""SELECT * FROM pg_extensions;""")
        return {"extensions":request_to_dict(rows)}
    except Exception as e:
        return {"error": str(e)}
    finally:
        await conn.close()

async def get_all_views():
    conn = await get_db_conn_pg()
    try:
        rows = await conn.fetch(
            """SELECT 
    schemaname,
    viewname,
    viewowner,
    definition
    FROM pg_views
    WHERE schemaname = 'public'
    ORDER BY viewname;""")
        return {"views":request_to_dict(rows=rows)}
    except Exception as e:
        return {"error": str(e)}
    finally:
        await conn.close()
async def get_all_materialized_views(): 
    conn = await get_db_conn_pg()
    try: 
        rows = await conn.fetch("""SELECT * FROM pg_matviews ORDER BY schemaname, matviewname;""")
        return {"materialized_views":request_to_dict(rows)}
    except Exception as e:
        return {"error": str(e)}
    finally:
        await conn.close()
def request_to_dict(rows):
    requests_list = [dict(row) for row in rows]
    return requests_list
