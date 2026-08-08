import asyncio
import json
import os
from typing import Dict, Any

from fastapi import FastAPI, WebSocket, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware

from src.api.v1.postgres_routes import router as postgres_router
from src.api.v1.cache_routes import router as cache_router, memcache_router
from src.api.v1.mongo_routes import router as mongo_router
from src.core.database import close_pg
from src.core.redis_db import close_redis
from src.core.memcache_db import close_memcache
from src.core.mongo_db import close_mongo

API_V1_PREFIX = "/api/v1"

app = FastAPI(
    title="Midnight",
    version="0.1.0",
    description="Midnight API - Database Statistics Collector",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.include_router(postgres_router, prefix=f"{API_V1_PREFIX}")
app.include_router(cache_router, prefix=f"{API_V1_PREFIX}")
app.include_router(memcache_router, prefix=f"{API_V1_PREFIX}")
app.include_router(mongo_router, prefix=f"{API_V1_PREFIX}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080", "http://127.0.0.1:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("shutdown")
async def shutdown_event():
    """Закрывает подключения к базам данных при остановке приложения"""
    await close_pg()
    await close_redis()
    await close_memcache()
    await close_mongo()


@app.get("/")
async def root():
    return {
        "message": "Welcome to Midnight API",
        "endpoints": {
            "postgres": f"{API_V1_PREFIX}/postgres",
            "redis": f"{API_V1_PREFIX}/redis",
            "memcache": f"{API_V1_PREFIX}/memcache",
            "mongo": f"{API_V1_PREFIX}/mongo",
            "docs": "/docs",
        },
    }
