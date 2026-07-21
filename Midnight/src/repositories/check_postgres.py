from src.core.database import get_db_conn

async def check_version():
    conn = await get_db_conn()
    version = await conn.fetchval("SELECT version()")
    await conn.close()
    return {"version": version}

async def check_requests():
    conn = await get_db_conn()
    rows = await conn.fetch("SELECT * FROM pg_stat_activity;")
    await conn.close()
    result =  request_to_dict(rows)
    return result

async def get_users():
    conn = await  get_db_conn()
    rows = await  conn.fetch("SELECT usename, usesuper, usecreatedb, valuntil FROM pg_user;" )
    await conn.close()
    result = request_to_dict(rows)
    return result

async def get_tables():
    conn = await get_db_conn()
    rows = await conn.fetch("SELECT tablename FROM pg_tables WHERE schemaname = 'public';")
    await conn.close()
    result = request_to_dict(rows)
    return result
async def get_databases():
    conn = await get_db_conn()
    rows = await conn.fetch("SELECT datname FROM pg_database;")
    await conn.close()
    result = request_to_dict(rows)
    return result

async def get_transactions():
    conn = await get_db_conn()
    rows = await conn.fetch("SELECT pid,usename, application_name,client_addr,state,query, query_start, now() - query_start AS duration FROM pg_stat_activity ORDER BY duration DESC;")
    await conn.close()
    result = request_to_dict(rows)
    return result

def request_to_dict(rows):
    requests_list = [dict(row) for row in rows]
    return requests_list