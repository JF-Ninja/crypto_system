from datetime import datetime

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError

from user_microservice.interfaces import AbstractUserClass, AbstractHasherClass
from user_microservice.schema.user_schema import SUserRegister, SUserBase, SUserUpdate


class UserService:
    def __init__(self, repository: AbstractUserClass, hasher: AbstractHasherClass):
        self.repository = repository
        self.hasher = hasher


    async def register(self, user_data: SUserRegister):
        try:
            data = user_data.model_dump()
            data["hashed_password"] = self.hasher.hash_password(data.pop("password"))
            user_data = await self.repository.add(data)
            await self.repository.save_changes()
            return user_data.id
        except IntegrityError:
            await self.repository.rollback_changes()
            raise HTTPException(status_code=409, detail="User already exists")

    async def authenticate_user(self, email: str, password: str):
        user = await self.repository.find_active_user(email=email)
        if not user or not self.hasher.verify_password(password, user.hashed_password):
            return None
        return user

    async def update_user(self, user_data: SUserUpdate, current_user: SUserBase):
        data = user_data.model_dump()
        if not data:
            raise HTTPException(status_code=400, detail="No fields provided for update")
        data["hashed_password"] = self.hasher.hash_password(data.pop("password"))
        data["updated_at"] = datetime.now()
        result = await self.repository.update(filter_by={"id": current_user.id}, values=data)
        await self.repository.save_changes()
        return result

    async def delete_user(self, current_user: int):
        result = await self.repository.delete(filter_by={"id": current_user})
        await self.repository.save_changes()
        return result


    async def get_user(self, user_id: int):
        return await self.repository.find_active_user(id=user_id)