from typing import List

from fastapi import APIRouter, Depends

from asset_microservice.dependencies import get_asset_service
from asset_microservice.schema.asset_schema import SAssetCreate, SAssetName

external_router = APIRouter(prefix="/assets", tags=["Asset Management"])

internal_router = APIRouter(prefix="/internal/assets", tags=["Internal asset Management"])


@external_router.post('/add')
async def create_asset(asset: List[SAssetName], service = Depends(get_asset_service)):
    return await service.create_asset(asset)

@external_router.get('/get_assets')
async def get_assets(service = Depends(get_asset_service)):
    return await service.get_assets()

@external_router.patch('/update_asset')
async def auto_update_asset(service = Depends(get_asset_service)):
    return await service.update_assets()

@external_router.delete('/delete_asset')
async def delete_asset(asset: SAssetName, service = Depends(get_asset_service)):
    return await service.delete_asset(asset)


@internal_router.post('/get_asset')
async def get_asset(asset: SAssetName, service = Depends(get_asset_service)):
    return await service.get_assets(asset)