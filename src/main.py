import asyncio
import os

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse

from src.api.v1.cache_routes import memcache_router
from src.api.v1.cache_routes import router as cache_router
from src.api.v1.connections_routes import router as connections_router
from src.api.v1.mongo_routes import router as mongo_router
from src.api.v1.postgres_routes import router as postgres_router
from src.core.connection_manager import close_all_clients
from src.core.database import close_pg
from src.core.memcache_db import close_memcache
from src.core.mongo_db import close_mongo
from src.core.redis_db import close_redis
from src.services.stats_collector import collect_all_stats

API_V1_PREFIX = "/api/v1"
STATS_INTERVAL_SECONDS = 3
TEMPLATES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")

app = FastAPI(
    title="Midnight",
    version="0.1.0",
    description="Midnight API - Database Statistics Collector",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.include_router(postgres_router, prefix=f"{API_V1_PREFIX}")
app.include_router(cache_router, prefix=f"{API_V1_PREFIX}")
app.include_router(memcache_router, prefix=f"{API_V1_PREFIX}")
app.include_router(mongo_router, prefix=f"{API_V1_PREFIX}")
app.include_router(connections_router, prefix=f"{API_V1_PREFIX}")

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
    await close_all_clients()


@app.get("/", response_class=HTMLResponse)
async def index() -> FileResponse:
    """Отдаёт веб-дашборд мониторинга"""
    return FileResponse(os.path.join(TEMPLATES_DIR, "index.html"))


@app.websocket("/ws/stats")
async def websocket_stats(websocket: WebSocket):
    """Стримит статистику всех баз данных по WebSocket"""
    await websocket.accept()
    try:
        while True:
            stats = await collect_all_stats()
            await websocket.send_json(stats)
            await asyncio.sleep(STATS_INTERVAL_SECONDS)
    except WebSocketDisconnect:
        return
    except Exception:
        return
