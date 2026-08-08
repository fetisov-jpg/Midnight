from fastapi import APIRouter
from src.repositories.check_cache_dbs import check_redis_info, check_memcache_stats
from src.core.redis_db import get_redis_config
from src.core.memcache_db import get_memcache_config

router = APIRouter(prefix="/redis", tags=["redis"])


@router.get("/")
def root():
    return {"message": "Redis endpoints"}


@router.get("/ping")
async def ping():
    return {"status": "pong"}


@router.get("/config")
async def get_config():
    """Возвращает текущую конфигурацию Redis"""
    config = get_redis_config()
    return {
        "host": config.host,
        "port": config.port,
        "db": config.db,
    }


@router.get("/info")
async def get_redis_info():
    """Получает полную статистику Redis"""
    return await check_redis_info()


# Memcached роуты
memcache_router = APIRouter(prefix="/memcache", tags=["memcache"])


@memcache_router.get("/")
def memcache_root():
    return {"message": "Memcached endpoints"}


@memcache_router.get("/ping")
async def memcache_ping():
    return {"status": "pong"}


@memcache_router.get("/config")
async def get_memcache_config_endpoint():
    """Возвращает текущую конфигурацию Memcached"""
    config = get_memcache_config()
    return {
        "host": config.host,
        "port": config.port,
    }


@memcache_router.get("/stats")
async def get_memcache_stats():
    """Получает статистику Memcached"""
    return await check_memcache_stats()
