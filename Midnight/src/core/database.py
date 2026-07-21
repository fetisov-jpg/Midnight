import asyncpg
from dotenv import load_dotenv
import os
print("Current dir:", os.getcwd())
print(".env exists:", os.path.exists(".env"))

# Явно указываем путь к .env для уверенности
load_dotenv(dotenv_path=".env")
load_dotenv()

# Просто читаем переменные один раз при импорте
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
DB_NAME = os.getenv("DB_NAME")

async def get_db_conn():
    connection = await asyncpg.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASS,
        database=DB_NAME
    )
    return connection