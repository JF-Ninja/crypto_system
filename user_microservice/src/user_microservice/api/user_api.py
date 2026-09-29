from fastapi import APIRouter, Depends
from user_microservice.dependencies import get_user_service, get_current_user
from user_microservice.schema.user_schema import SUserBase, SUserUpdate


external_router = APIRouter(prefix='/users', tags=["User Management"])

internal_router = APIRouter(prefix='/internal/users', tags=["Internal User Management"])



@external_router.get('/me', response_model=SUserBase)
async def read_me(current_user = Depends(get_current_user)):
    return current_user

@external_router.patch('/me')
async def update_me(user_new_data: SUserUpdate, service = Depends(get_user_service), current_user = Depends(get_current_user)):
    return await service.update_user(user_new_data, current_user)

@external_router.delete('/me')
async def delete_me(service = Depends(get_user_service), current_user = Depends(get_current_user)):
    return await service.delete_user(current_user.id)

@internal_router.post('/get_user')
async def get_user_id(user_id: int, service = Depends(get_user_service)):
    return await service.get_user(user_id)