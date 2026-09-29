from abc import ABC, abstractmethod


class AbstractRepository(ABC):

    @abstractmethod
    async def rollback_changes(self):
        pass

    @abstractmethod
    async def save_changes(self):
        pass

    @abstractmethod
    async def add(self, info):
        pass

    @abstractmethod
    async def find_one_or_none(self, **filter_by):
        pass

    @abstractmethod
    async def find_all(self, **filter_by):
        pass

    @abstractmethod
    async def update(self, filter_by, values):
        pass

    @abstractmethod
    async def delete(self, filter_by):
        pass

class AbstractRedisClass(ABC):

    @abstractmethod
    async def set_pairs(self, **kwargs):
        pass

    @abstractmethod
    async def get_pairs(self, *args):
        pass

    @abstractmethod
    async def get_all_pairs(self):
        pass

    @abstractmethod
    async def delete_pairs(self, *args):
        pass



class AbstractUserClass(AbstractRepository, ABC):

    @abstractmethod
    async def find_active_user(self, **kwargs):
        pass

class AbstractHasherClass(ABC):

    @abstractmethod
    def hash_password(self, password):
        pass

    @abstractmethod
    def verify_password(self, password_plain: str, password_hashed: str):
        pass


class AbstractSecurityClass(ABC):

    @abstractmethod
    async def get_current_user(self, token: str):
        pass

    @abstractmethod
    async def set_auth_tokens(self, data):
        pass

    @abstractmethod
    async def update_refresh_token(self, token: str):
        pass


