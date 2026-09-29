import asyncio

from contextlib import asynccontextmanager

from fastapi import FastAPI

from alert_microservice.logger import logger
from alert_microservice.api.alert_api import router as alert_router
from alert_microservice.dependencies import get_redis_connection, get_db_connection
from alert_microservice.rabbitmq_connection import rabbitmq_connection
from alert_microservice.rabbitmq_consumer import RabbitMQConsumer
from alert_microservice.redis_repository import RedisRepository
from alert_microservice.repository.alert_repository import AlertRepository


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with rabbitmq_connection() as queue:
        redis_cm = asynccontextmanager(get_redis_connection)
        postgre_cm = asynccontextmanager(get_db_connection)
        async with postgre_cm() as real_postgre_client:
            async with redis_cm() as real_redis_client:
                redis_rep = RedisRepository(real_redis_client)
                alert_rep = AlertRepository(real_postgre_client)
                rabbitmq_consumer = RabbitMQConsumer(redis_rep, queue["crypto_q"], queue["trigger_q"], queue["trigger_ex"], alert_rep)
                task1 = asyncio.create_task(rabbitmq_consumer.monitoring_alerts())
                task2 = asyncio.create_task(rabbitmq_consumer.activating_alerts())
                yield
                task1.cancel()
                task2.cancel()
                try:
                    await task1
                    await task2
                except asyncio.CancelledError:
                    logger.info("RabbitMQ stopped")


app = FastAPI(root_path="/api/v1/alerts", lifespan=lifespan)

app.include_router(alert_router)