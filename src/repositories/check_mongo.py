from src.core.mongo_db import get_mongo_config, get_mongo_conn


async def check_mongo_info(client=None, config=None):
    """Получает статистику MongoDB"""
    try:
        client = client or await get_mongo_conn()
        cfg = config or get_mongo_config()
        server_status = await client.admin.command("serverStatus")

        return {
            "status": "connected",
            "config": {
                "host": cfg.host,
                "port": cfg.port,
                "database": cfg.database,
            },
            "info": {
                "version": server_status.get("version"),
                "uptime_in_seconds": server_status.get("uptime"),
                "connections": server_status.get("connections", {}).get("current"),
                "memory_used_bytes": server_status.get("mem", {}).get("resident"),
                "mapped_bytes": server_status.get("mem", {}).get("mapped"),
                "network_in_bytes": server_status.get("network", {}).get("bytesIn"),
                "network_out_bytes": server_status.get("network", {}).get("bytesOut"),
                "operations_insert": server_status.get("opcounters", {}).get("insert"),
                "operations_query": server_status.get("opcounters", {}).get("query"),
                "operations_update": server_status.get("opcounters", {}).get("update"),
                "operations_delete": server_status.get("opcounters", {}).get("delete"),
            },
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
        }


async def check_mongo_databases(client=None):
    """Получает список баз данных MongoDB"""
    try:
        client = client or await get_mongo_conn()
        databases = await client.list_database_names()

        return {
            "status": "connected",
            "databases": databases,
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
        }


async def check_mongo_db_stats(client=None, config=None):
    """Получает статистику базы данных MongoDB"""
    try:
        client = client or await get_mongo_conn()
        cfg = config or get_mongo_config()
        db_name = cfg.database
        db_stats = await client[db_name].command("dbStats")

        return {
            "status": "connected",
            "database": db_name,
            "stats": {
                "collections": db_stats.get("collections"),
                "views": db_stats.get("views"),
                "objects": db_stats.get("objects"),
                "avg_object_size_bytes": db_stats.get("avgObjSize"),
                "data_size_bytes": db_stats.get("dataSize"),
                "storage_size_bytes": db_stats.get("storageSize"),
                "indexes": db_stats.get("indexes"),
                "index_size_bytes": db_stats.get("indexSize"),
            },
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
        }
