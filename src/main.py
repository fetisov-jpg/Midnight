from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from src.api.v1.health_check_postgres import router as health_check_postgres
from src.api.v1.health_check_mongo import router as health_check_mongo

app = FastAPI(
    title="Midnight",
    version="0.1.0",
    description="Midnight API",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Подключаем роутер с префиксом /api/v1
app.include_router(health_check_postgres, prefix="/api/v1")
app.include_router(health_check_mongo, prefix="/api/v1")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080", "http://127.0.0.1:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
@app.get("/")
async def root():
    return {"message": "Welcome to Midnight API"}