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
    async def update(self, filter_by: dict, values):
        pass

    @abstractmethod
    async def find_all(self, **filter_by):
        pass

    @abstractmethod
    async def find_one_or_none(self, **filter_by):
        pass

class AbstractRedisClass(ABC):

    @abstractmethod
    async def set_pairs(self, ttl: int = None, **kwargs):
        pass

    @abstractmethod
    async def set_hash_pairs(self, hash_key: str, **kwargs):
        pass

    @abstractmethod
    async def get_pairs(self, *args):
        pass

    @abstractmethod
    async def get_hash_pairs(self, hash_key: str, *args):
        pass

    @abstractmethod
    async def delete_pairs(self, *args):
        pass

    @abstractmethod
    async def delete_hash_pairs(self, hash_key: str, *args):
        pass

class AbstractAlertClass(AbstractRepository, ABC):
    pass


class AbstractSecurityClass(ABC):

    @staticmethod
    @abstractmethod
    def get_current_user_id(token: str):
        pass