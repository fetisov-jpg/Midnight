import aiomcache
from src.core.config import MemcacheConfig

# Создаем конфигурацию один раз при импорте
memcache_config = MemcacheConfig.from_env()
_memcache_client: aiomcache.Client | None = None


async def get_memcache_conn() -> aiomcache.Client:
    """Получает подключение к Memcached"""
    global _memcache_client

    if _memcache_client is None:
        _memcache_client = aiomcache.Client(
            host=memcache_config.host, port=memcache_config.port
        )

    return _memcache_client


def get_memcache_config() -> MemcacheConfig:
    """Возвращает текущую конфигурацию Memcached"""
    return memcache_config


async def close_memcache():
    """Закрывает подключение к Memcached"""
    global _memcache_client
    if _memcache_client:
        await _memcache_client.close()
        _memcache_client = None
