from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI

from user_microservice.logger import logger

from user_microservice.exception_handlers import register_exception_handlers
from user_microservice.middleware import register_middleware
from user_microservice.router import register_routers


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    logger.info("User microservice starting")
    yield
    logger.info("User microservice stopping")
    await logger.complete()


app = FastAPI(root_path="/api/v1/users", lifespan=lifespan)

register_middleware(app)
register_exception_handlers(app)
register_routers(app)
