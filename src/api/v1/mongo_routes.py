from fastapi import APIRouter
from src.repositories.check_mongo import (
    check_mongo_info,
    check_mongo_databases,
    check_mongo_db_stats,
)
from src.core.mongo_db import get_mongo_config

router = APIRouter(prefix="/mongo", tags=["mongo"])


@router.get("/")
def root():
    return {"message": "MongoDB endpoints"}


@router.get("/ping")
async def ping():
    return {"status": "pong"}


@router.get("/config")
async def get_config():
    """Возвращает текущую конфигурацию MongoDB"""
    config = get_mongo_config()
    return {
        "host": config.host,
        "port": config.port,
        "database": config.database,
    }


@router.get("/info")
async def get_mongo_info():
    """Получает полную статистику MongoDB"""
    return await check_mongo_info()


@router.get("/databases")
async def get_mongo_databases():
    """Получает список баз данных MongoDB"""
    return await check_mongo_databases()


@router.get("/stats")
async def get_mongo_db_stats():
    """Получает статистику базы данных MongoDB"""
    return await check_mongo_db_stats()
