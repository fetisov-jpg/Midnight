import asyncpg
from dotenv import load_dotenv
import os
import pymongo
from pymongo import AsyncMongoClient
print("Current dir:", os.getcwd())
print(".env exists:", os.path.exists(".env"))

# Явно указываем путь к .env для уверенности
load_dotenv(dotenv_path=".env")
load_dotenv()

# Просто читаем переменные один раз при импорте
POSTGRES_DB_HOST = os.getenv("POSTGRES_DB_HOST")
POSTGRES_DB_PORT = os.getenv("POSTGRES_DB_PORT")
POSTGRES_DB_USER = os.getenv("POSTGRES_DB_USER")
POSTGRES_DB_PASS = os.getenv("POSTGRES_DB_PASS")
POSTGRES_DB_NAME = os.getenv("POSTGRES_DB_NAME")

MONGO_DB_HOST = os.getenv("MONGO_DB_HOST", "localhost")
MONGO_DB_PORT = int(os.getenv("MONGO_DB_PORT", 27017))  # ← Преобразуем в int
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "midnight")

async def get_db_conn_pg():
    connection = await asyncpg.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASS,
        database=DB_NAME
    )
    return connection
async def get_db_conn_mongo():
    """Создает асинхронное соединение с MongoDB"""
    client = AsyncMongoClient(
        host=MONGO_DB_HOST,
        port=MONGO_DB_PORT
    )
    return client