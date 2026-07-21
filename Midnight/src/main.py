from fastapi import FastAPI
from src.api.v1 import health_check_postgres

app = FastAPI(
    title="Midnight",
    version="0.1.0",
    description="Midnight API",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Подключаем роутер с префиксом /api/v1
app.include_router(health_check_postgres, prefix="/api/v1")

@app.get("/")
async def root():
    return {"message": "Welcome to Midnight API"}