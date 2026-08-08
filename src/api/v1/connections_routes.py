import uuid

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.core.connection_manager import close_client
from src.core.registry import (
    CONNECTION_TYPES,
    DEFAULT_DATABASES,
    DEFAULT_PORTS,
    ConnectionConfig,
    get_registry,
)
from src.services.stats_collector import collect_connection_stats

router = APIRouter(prefix="/connections", tags=["connections"])


class ConnectionCreate(BaseModel):
    name: str
    type: str
    host: str = "localhost"
    port: int | None = None
    user: str | None = None
    password: str | None = None
    database: str | None = None


@router.get("/")
async def list_connections() -> dict:
    connections = [c.to_dict(include_password=False) for c in get_registry().list()]
    return {"connections": connections}


@router.post("/", status_code=201)
async def create_connection(payload: ConnectionCreate) -> dict:
    if payload.type not in CONNECTION_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown type: {payload.type}. Allowed: {list(CONNECTION_TYPES)}",
        )
    if not payload.name.strip():
        raise HTTPException(status_code=400, detail="Name is required")

    config = ConnectionConfig(
        id=uuid.uuid4().hex,
        name=payload.name.strip(),
        type=payload.type,
        host=payload.host,
        port=payload.port or DEFAULT_PORTS[payload.type],
        user=payload.user,
        password=payload.password,
        database=payload.database or DEFAULT_DATABASES.get(payload.type),
    )
    get_registry().add(config)
    return config.to_dict(include_password=False)


@router.delete("/{connection_id}")
async def delete_connection(connection_id: str) -> dict:
    if not get_registry().remove(connection_id):
        raise HTTPException(status_code=404, detail="Connection not found")
    await close_client(connection_id)
    return {"status": "deleted", "id": connection_id}


@router.get("/{connection_id}/test")
async def test_connection(connection_id: str) -> dict:
    config = get_registry().get(connection_id)
    if config is None:
        raise HTTPException(status_code=404, detail="Connection not found")
    return await collect_connection_stats(config)
