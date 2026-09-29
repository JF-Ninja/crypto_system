from fastapi import HTTPException

from user_microservice.interfaces import AbstractSecurityClass
from user_microservice.schema.user_schema import SUserRegister
from user_microservice.service.user_service import UserService


class AuthService:
    def __init__(self, user_service: UserService, security: AbstractSecurityClass):
        self.user_service = user_service
        self.security = security

    async def register(self, user_data: SUserRegister):
        data = await self.user_service.register(user_data)
        return await self.security.set_auth_tokens(data)

    async def login(self, user_data: SUserRegister):
        user = await self.user_service.authenticate_user(user_data.email, user_data.password)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid email or password")
        return await self.security.set_auth_tokens(user.id)

    async def refresh_token(self, token: str):
        return await self.security.update_refresh_token(token)

