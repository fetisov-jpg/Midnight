import redis.asyncio as aioredis
from src.core.config import RedisConfig

# Создаем конфигурацию один раз при импорте
redis_config = RedisConfig.from_env()
_redis_pool: aioredis.Redis | None = None


async def get_redis_conn() -> aioredis.Redis:
    """Получает подключение к Redis из пула"""
    global _redis_pool

    if _redis_pool is None:
        _redis_pool = aioredis.from_url(
            redis_config.url, encoding="utf-8", decode_responses=True
        )

    return _redis_pool


def get_redis_config() -> RedisConfig:
    """Возвращает текущую конфигурацию Redis"""
    return redis_config


async def close_redis():
    """Закрывает подключение к Redis"""
    global _redis_pool
    if _redis_pool:
        await _redis_pool.close()
        _redis_pool = None
