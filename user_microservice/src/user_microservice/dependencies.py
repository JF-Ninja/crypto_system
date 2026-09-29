from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from user_microservice.jwt_service import JWTAuthService
from user_microservice.redis_repository import RedisRepository
from user_microservice.repository.user_repository import UserRepository
from user_microservice.service.auth_service import AuthService
from user_microservice.service.user_service import UserService

from user_microservice.db import async_session_maker
from user_microservice.redis_db import r
from user_microservice.utils import passhash

security_schema = HTTPBearer()

async def get_db_connection():
    async with async_session_maker() as session:
        yield session

async def get_redis_connection():
        yield r



async def get_user_repository(db: AsyncSession = Depends(get_db_connection)):
    return UserRepository(db)

async def get_redis_repository(db: AsyncSession = Depends(get_redis_connection)):
    return RedisRepository(db)


async def get_jwt_security(repository: UserRepository = Depends(get_user_repository), redis: RedisRepository = Depends(get_redis_repository)):
    return JWTAuthService(repository, redis)

async def get_token_from_request(credentials: HTTPAuthorizationCredentials = Depends(security_schema)) -> str:
    return credentials.credentials

async def get_current_user(token: str = Depends(get_token_from_request), security: JWTAuthService = Depends(get_jwt_security)):
    return await security.get_current_user(token)


async def get_user_service(repository: UserRepository = Depends(get_user_repository)):
    return UserService(repository, passhash)

async def get_auth_service(user_service: UserService = Depends(get_user_service),security: JWTAuthService = Depends(get_jwt_security)):
    return AuthService(user_service, security)
