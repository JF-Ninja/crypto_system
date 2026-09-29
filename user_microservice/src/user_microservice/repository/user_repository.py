from user_microservice.db_repository import MainRepository
from user_microservice.interfaces import AbstractUserClass
from user_microservice.model.user_model import User

class UserRepository(MainRepository, AbstractUserClass):

    def __init__(self, db):
        super().__init__(db, User)

    async def find_active_user(self, **kwargs):
        return await self.find_one_or_none(**kwargs, is_active=True)
