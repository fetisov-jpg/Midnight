from fastapi import APIRouter
from .health_check_postgres import router as health_check_postgres
router = APIRouter()
router.include_router(health_check_postgres)