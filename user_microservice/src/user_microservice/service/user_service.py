from datetime import datetime

from user_microservice.business_errors import EmptyUpdateFieldsError, UserNotFoundError
from user_microservice.interfaces import AbstractUserClass, AbstractHasherClass
from user_microservice.schema.user_schema import SUserRegister, SUserBase, SUserUpdate

class UserService:
    def __init__(self, repository: AbstractUserClass, hasher: AbstractHasherClass):
        self.repository = repository
        self.hasher = hasher


    async def register(self, user_data: SUserRegister):
        data = user_data.model_dump()
        data["hashed_password"] = self.hasher.hash_password(data.pop("password"))
        created_user = await self.repository.add(data)
        return created_user.id

    async def authenticate_user(self, email: str, password: str):
        user = await self.repository.find_active_user(email=email)
        if not user or not self.hasher.verify_password(password, user.hashed_password):
            return None
        return user

    async def update_user(self, user_data: SUserUpdate, current_user: SUserBase):
        data = user_data.model_dump(exclude_none=True)
        if not data:
            raise EmptyUpdateFieldsError()
        password = data.pop("password", None)
        if password is not None:
            data["hashed_password"] = self.hasher.hash_password(password)
        data["updated_at"] = datetime.now()
        result = await self.repository.update(filter_by={"id": current_user.id}, values=data)
        return result

    async def delete_user(self, current_user: int):
        result = await self.repository.delete(filter_by={"id": current_user})
        return result

    async def get_user(self, user_id: int):
        user = await self.repository.find_active_user(id=user_id)
        if not user:
            raise UserNotFoundError()
        return user