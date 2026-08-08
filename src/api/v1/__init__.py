from fastapi import APIRouter

from .cache_routes import memcache_router
from .cache_routes import router as redis_router
from .connections_routes import router as connections_router
from .mongo_routes import router as mongo_router
from .postgres_routes import router as postgres_router

router = APIRouter()
router.include_router(postgres_router, prefix="/postgres")
router.include_router(redis_router, prefix="/redis")
router.include_router(memcache_router, prefix="/memcache")
router.include_router(mongo_router, prefix="/mongo")
router.include_router(connections_router, prefix="/connections")

__all__ = [
    "connections_router",
    "memcache_router",
    "mongo_router",
    "postgres_router",
    "redis_router",
    "router",
]
