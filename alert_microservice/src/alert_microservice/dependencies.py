import httpx
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from alert_microservice.db import async_session_maker
from alert_microservice.redis_db import r
from alert_microservice.redis_repository import RedisRepository
from alert_microservice.repository.alert_repository import AlertRepository
from alert_microservice.service.alert_service import AlertService
from fastapi import Depends, HTTPException

security_schema = HTTPBearer()

async def get_db_connection():
    async with async_session_maker() as session:
        yield session

async def get_redis_connection():
    async with r as redis:
        yield redis


async def get_alert_repository(db = Depends(get_db_connection)):
    return AlertRepository(db)

async def get_redis_repository(redis = Depends(get_redis_connection)):
    return RedisRepository(redis)

async def get_alert_service(repository = Depends(get_alert_repository), redis = Depends(get_redis_repository)):
    return AlertService(repository, redis)

async def get_token_from_requests(credentials: HTTPAuthorizationCredentials = Depends(security_schema)) -> str:
    return credentials.credentials

async def get_current_user(token = Depends(get_token_from_requests)):
    headers = {"Authorization": f"Bearer {token}", "Content-type": "application/json",}
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post("http://users-app:8000/internal/auth/get_user_id", headers=headers)
        except httpx.RequestError:
            raise HTTPException(status_code=503, detail="User service is unavailable")
    user_info = response.json()
    return user_info