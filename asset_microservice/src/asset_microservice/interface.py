from abc import ABC, abstractmethod


class RedisRepository(ABC):

    @abstractmethod
    async def set_pairs(self, **kwargs):
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



class AbstractAssetRepository(RedisRepository, ABC):
    pass