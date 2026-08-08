from motor.motor_asyncio import AsyncIOMotorClient
from src.core.config import MongoConfig

# Создаем конфигурацию один раз при импорте
mongo_config = MongoConfig.from_env()
_mongo_client: AsyncIOMotorClient | None = None


async def get_mongo_conn() -> AsyncIOMotorClient:
    """Получает подключение к MongoDB"""
    global _mongo_client

    if _mongo_client is None:
        _mongo_client = AsyncIOMotorClient(mongo_config.uri)

    return _mongo_client


def get_mongo_config() -> MongoConfig:
    """Возвращает текущую конфигурацию MongoDB"""
    return mongo_config


async def close_mongo():
    """Закрывает подключение к MongoDB"""
    global _mongo_client
    if _mongo_client:
        _mongo_client.close()
        _mongo_client = None
