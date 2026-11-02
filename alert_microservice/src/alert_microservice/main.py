import asyncio

from contextlib import asynccontextmanager

from fastapi import FastAPI

from alert_microservice.exception_handlers import register_exception_handlers
from alert_microservice.logger import logger
from alert_microservice.middleware import register_middleware
from alert_microservice.router import register_routers
from alert_microservice.dependencies import get_redis_connection, get_db_connection
from alert_microservice.rabbitmq_connection import rabbitmq_connection
from alert_microservice.rabbitmq_consumer import RabbitMQConsumer
from alert_microservice.redis_repository import RedisRepository
from alert_microservice.repository.alert_repository import AlertRepository


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Alerts microservice starting")
    async with rabbitmq_connection() as queue:
        logger.info("RabbitMQ successfully connected")
        redis_cm = asynccontextmanager(get_redis_connection)
        postgre_cm = asynccontextmanager(get_db_connection)
        async with postgre_cm() as real_postgre_client:
            async with redis_cm() as real_redis_client:
                logger.info("Db and Redis successfully connected")
                redis_rep = RedisRepository(real_redis_client)
                alert_rep = AlertRepository(real_postgre_client)
                rabbitmq_consumer = RabbitMQConsumer(redis_rep, queue["crypto_q"], queue["trigger_q"], queue["trigger_ex"], alert_rep)
                task1 = asyncio.create_task(rabbitmq_consumer.monitoring_alerts())
                task2 = asyncio.create_task(rabbitmq_consumer.activating_alerts())
                logger.info("RabbitMQ tasks created")
                yield
                task1.cancel()
                task2.cancel()
                for task in (task1, task2):
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass
    await logger.complete()


app = FastAPI(root_path="/api/v1/alerts", lifespan=lifespan)

register_middleware(app)
register_exception_handlers(app)
register_routers(app)