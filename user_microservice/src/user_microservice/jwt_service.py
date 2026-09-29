from datetime import datetime, timedelta, timezone
import jwt
import uuid
from fastapi import HTTPException, status
from jwt.exceptions import InvalidTokenError

from user_microservice.config import jwt_config
from user_microservice.interfaces import AbstractSecurityClass, AbstractUserClass, AbstractRedisClass

credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


def _get_private_key() -> str:
    with open(jwt_config.private_key_path, "r") as private_key:
        return private_key.read()

def _get_public_key() -> str:
    with open(jwt_config.public_key_path, "r") as public_key:
        return public_key.read()

class JWTAuthService(AbstractSecurityClass):
    def __init__(self, user_repository: AbstractUserClass, redis_repository: AbstractRedisClass):
        self.user_repository = user_repository
        self.redis_repository = redis_repository


    async def get_current_user(self, token: str):
        try:
            payload = jwt.decode(token, _get_public_key(), algorithms=[jwt_config.algorithm])
            token_data = int(payload.get("sub"))
            token_type = payload.get("type")
            if token_type != "access":
                raise credentials_exception
        except jwt.InvalidTokenError:
            raise credentials_exception
        user = await self.user_repository.find_active_user(id=token_data)
        if user is None:
            raise credentials_exception
        return user

    async def set_auth_tokens(self, data: int, expires_access_delta: timedelta | None = None,
                        expires_refresh_delta: timedelta | None = None):
        random_uuid = uuid.uuid4()
        access_token = self.create_access_token(str(data), str(random_uuid), expires_access_delta)
        refresh_token = self.create_refresh_token(str(data), str(random_uuid), expires_refresh_delta)
        key_name = f"auth:refresh:{data}:{random_uuid}"
        if expires_refresh_delta:
            await self.redis_repository.set_pairs(ttl=expires_refresh_delta, **{key_name: refresh_token})
        else:
            await self.redis_repository.set_pairs(ttl=jwt_config.refresh_token_expire_days * 86400, **{key_name: refresh_token} )
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        }

    @staticmethod
    def create_access_token(data: str, jti_uuid: str, expires_delta: timedelta | None = None):
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=jwt_config.access_token_expire_minutes)
        to_encode = {"sub": data, "jti": jti_uuid, "type": "access", "exp": expire}
        return jwt.encode(to_encode, _get_private_key(), algorithm=jwt_config.algorithm)

    @staticmethod
    def create_refresh_token(data: str, jti_uuid: str, expires_delta: timedelta | None = None):
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(days=jwt_config.refresh_token_expire_days)
        to_encode = {"sub": data, "jti": jti_uuid, "type": "refresh", "exp": expire}
        return jwt.encode(to_encode, _get_private_key(), algorithm=jwt_config.algorithm)

    async def update_refresh_token(self, token: str):
        try:
            payload = jwt.decode(token, _get_public_key(), algorithms=[jwt_config.algorithm])
            if payload.get("type") != "refresh":
                raise credentials_exception
            token_uuid = payload.get("jti")
            token_data = int(payload.get("sub"))
            user = await self.user_repository.find_active_user(id=token_data)
            if not user:
                raise HTTPException(status_code=403, detail="User account is deactivated")
            key_name = f"auth:refresh:{user.id}:{token_uuid}"
            redis_uuid = await self.redis_repository.get_pairs(f"{key_name}")
            if not redis_uuid.get(f"{key_name}"):
                raise credentials_exception
            await self.redis_repository.delete_pairs(f"{key_name}")
            return await self.set_auth_tokens(token_data)
        except InvalidTokenError:
            raise credentials_exception
