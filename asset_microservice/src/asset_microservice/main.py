import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI

from asset_microservice.logger import logger
from asset_microservice.middleware import register_middleware
from asset_microservice.rabbitmq_connection import rabbitmq_connection
from asset_microservice.redis_db import r
from asset_microservice.repository.asset_repository import AssetRepository
from asset_microservice.service.asset_service import AssetService
from asset_microservice.router import register_routers
from asset_microservice.exception_handlers import register_exception_handlers


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with rabbitmq_connection() as exchange:
        repository = AssetRepository(r)
        asset_service = AssetService(repository)
        bg_task = asyncio.create_task(asset_service.auto_update_asset(exchange))
        logger.info("Background ticker streaming task started.")
        yield
        bg_task.cancel()
        try:
            await bg_task
        except asyncio.CancelledError:
            logger.info("Lifespan background tasks successfully stopped.")
    await logger.complete()

app = FastAPI(root_path="/api/v1/assets", lifespan=lifespan)

register_middleware(app)
register_exception_handlers(app)
register_routers(app)