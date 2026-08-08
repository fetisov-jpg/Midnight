from fastapi import APIRouter

from .postgres_routes import router as postgres_router
from .cache_routes import router as redis_router, memcache_router
from .mongo_routes import router as mongo_router

router = APIRouter()
router.include_router(postgres_router, prefix="/postgres")
router.include_router(redis_router, prefix="/redis")
router.include_router(memcache_router, prefix="/memcache")
router.include_router(mongo_router, prefix="/mongo")

__all__ = ["router", "postgres_router", "redis_router", "memcache_router", "mongo_router"]
