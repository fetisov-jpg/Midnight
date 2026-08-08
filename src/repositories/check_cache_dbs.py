from src.core.memcache_db import get_memcache_config, get_memcache_conn
from src.core.redis_db import get_redis_config, get_redis_conn


async def check_redis_info(client=None):
    """Получает статистику Redis"""
    try:
        redis = client or await get_redis_conn()
        info = await redis.info()

        # Получаем количество ключей
        db_size = await redis.dbsize()

        return {
            "status": "connected",
            "config": {
                "host": get_redis_config().host,
                "port": get_redis_config().port,
                "db": get_redis_config().db,
            },
            "info": {
                "redis_version": info.get("redis_version"),
                "uptime_in_seconds": info.get("uptime_in_seconds"),
                "connected_clients": info.get("connected_clients"),
                "used_memory": info.get("used_memory"),
                "used_memory_human": info.get("used_memory_human"),
                "total_connections_received": info.get("total_connections_received"),
                "keyspace_hits": info.get("keyspace_hits"),
                "keyspace_misses": info.get("keyspace_misses"),
            },
            "db_size": db_size,
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
        }


async def check_memcache_stats(client=None):
    """Получает статистику Memcached"""
    try:
        memcache = client or await get_memcache_conn()
        stats = await memcache.stats()

        if not stats:
            return {"status": "error", "message": "No stats available"}

        # Берем статистику первого сервера
        server_stats = next(iter(stats.values())) if stats else {}

        return {
            "status": "connected",
            "config": {
                "host": get_memcache_config().host,
                "port": get_memcache_config().port,
            },
            "stats": {
                "pid": server_stats.get("pid"),
                "uptime": server_stats.get("uptime"),
                "curr_items": server_stats.get("curr_items"),
                "total_items": server_stats.get("total_items"),
                "curr_connections": server_stats.get("curr_connections"),
                "total_connections": server_stats.get("total_connections"),
                "bytes": server_stats.get("bytes"),
                "get_hits": server_stats.get("get_hits"),
                "get_misses": server_stats.get("get_misses"),
                "bytes_read": server_stats.get("bytes_read"),
                "bytes_written": server_stats.get("bytes_written"),
            },
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
        }
