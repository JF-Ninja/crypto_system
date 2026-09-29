from asset_microservice.interface import AbstractAssetRepository
from asset_microservice.redis_repository import RedisRepository


class AssetRepository(RedisRepository, AbstractAssetRepository):

    def __init__(self, redis):
        super().__init__(redis)