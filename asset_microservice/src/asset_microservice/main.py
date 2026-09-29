import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from asset_microservice.api.asset_api import external_router as external_asset_router
from asset_microservice.api.asset_api import internal_router as internal_asset_router
from asset_microservice.api.websocket_api import router as websocket_router
from asset_microservice.rabbitmq_connection import rabbitmq_connection
from asset_microservice.redis_db import r
from asset_microservice.repository.asset_repository import AssetRepository
from asset_microservice.service.asset_service import AssetService


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with rabbitmq_connection() as exchange:
        repository = AssetRepository(r)
        asset_service = AssetService(repository)
        bg_task = asyncio.create_task(asset_service.auto_update_asset(exchange))
        yield
        bg_task.cancel()
        try:
            await bg_task
        except asyncio.CancelledError:
            print("Lifespan stopped")

app = FastAPI(root_path="/api/v1/assets", lifespan=lifespan)

app.include_router(external_asset_router)
app.include_router(internal_asset_router)
app.include_router(websocket_router)