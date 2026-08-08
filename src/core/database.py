import asyncpg
from src.core.config import PostgresConfig

# Создаем конфигурацию один раз при импорте
postgres_config = PostgresConfig.from_env()

async def get_db_conn():
    connection = await asyncpg.connect(
        host=postgres_config.host,
        port=postgres_config.port,
        user=postgres_config.user,
        password=postgres_config.password,
        database=postgres_config.database
    )
    return connection


def get_postgres_config() -> PostgresConfig:
    """Возвращает текущую конфигурацию PostgreSQL"""
    return postgres_config