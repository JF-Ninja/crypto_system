from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import Request

from alert_microservice.db import async_session_maker
from alert_microservice.httpx_service import MicroserviceClient
from alert_microservice.redis_db import r
from alert_microservice.redis_repository import RedisRepository
from alert_microservice.repository.alert_repository import AlertRepository
from alert_microservice.service.alert_service import AlertService
from fastapi import Depends

security_schema = HTTPBearer()

async def get_db_connection():
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise

async def get_redis_connection():
    async with r as redis:
        yield redis

def get_external_service(request: Request):
    return MicroserviceClient(request)

async def get_alert_repository(db = Depends(get_db_connection)):
    return AlertRepository(db)

async def get_redis_repository(redis = Depends(get_redis_connection)):
    return RedisRepository(redis)

async def get_alert_service(repository = Depends(get_alert_repository), redis = Depends(get_redis_repository), client = Depends(get_external_service)):
    return AlertService(repository, redis, client)

async def get_token_from_requests(credentials: HTTPAuthorizationCredentials = Depends(security_schema)) -> str:
    return credentials.credentials



async def get_current_user(token = Depends(get_token_from_requests),external_service: MicroserviceClient = Depends(get_external_service)):
    response_json = await external_service.send_request(method="POST", url="http://users-app:8000/internal/auth/get_user_id",headers={"Authorization": f"Bearer {token}"})
    return response_json