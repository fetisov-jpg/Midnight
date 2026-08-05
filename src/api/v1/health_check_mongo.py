from builtins import Exception

from fastapi import APIRouter, Depends, HTTPException, Query, status

from src.core.database import get_db_conn_mongo

router = APIRouter(
    prefix="/mongo",  
    tags=["mongo"]
)
@router.get("/")
async def get_hello_from_mongo():
    client = await get_db_conn_mongo()
    db = client.testdb
    return {"message": "Hello from MongoDB", "database": "testdb"}
