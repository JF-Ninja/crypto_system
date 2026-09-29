from fastapi import Depends

from asset_microservice.redis_db import r
from asset_microservice.repository.asset_repository import AssetRepository
from asset_microservice.service.asset_service import AssetService

async def get_redis_connection():
    async with r as redis:
        yield redis


async def get_asset_repository(redis = Depends(get_redis_connection)):
    return AssetRepository(redis)

async def get_asset_service(repository = Depends(get_asset_repository)):
    return AssetService(repository)