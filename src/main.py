from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from src.api.v1.postgres_routes import router as postgres_router
from src.api.v1.cache_routes import router as redis_router, memcache_router as memcache_router
from src.core.redis_db import close_redis
from src.core.memcache_db import close_memcache

app = FastAPI(
    title="Midnight",
    version="0.1.0",
    description="Midnight API - Database Statistics Collector",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Подключаем роутеры с префиксом /api/v1
app.include_router(postgres_router, prefix="/api/v1")
app.include_router(redis_router, prefix="/api/v1")
app.include_router(memcache_router, prefix="/api/v1")

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
    await close_redis()
    await close_memcache()


@app.get("/")
async def root():
    return {
        "message": "Welcome to Midnight API",
        "endpoints": {
            "postgres": "/api/v1/postgres",
            "redis": "/api/v1/redis",
            "memcache": "/api/v1/memcache",
            "docs": "/docs"
        }
    }