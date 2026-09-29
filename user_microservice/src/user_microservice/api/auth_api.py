from fastapi import APIRouter, Depends
from user_microservice.dependencies import get_token_from_request, get_auth_service, get_jwt_security
from user_microservice.jwt_service import JWTAuthService
from user_microservice.schema.user_schema import SUserRegister
from user_microservice.service.auth_service import AuthService

external_router = APIRouter(prefix='/auth', tags=["Authentication Management"])

internal_router = APIRouter(prefix='/internal/auth', tags=["Internal Authentication Management"])

@external_router.post('/register')
async def user_registration(user_data: SUserRegister, service: AuthService = Depends(get_auth_service)):
    return await service.register(user_data)

@external_router.post('/login')
async def user_login(user_data: SUserRegister, service: AuthService = Depends(get_auth_service)):
    return await service.login(user_data)

@external_router.post('/refresh_token')
async def refresh_token(token: str = Depends(get_token_from_request), service: AuthService = Depends(get_auth_service)):
    return await service.refresh_token(token)

@internal_router.post('/get_user_id')
async def get_user_id(token: str = Depends(get_token_from_request), service: JWTAuthService = Depends(get_jwt_security)):
    return await service.get_current_user(token)

