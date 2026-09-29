from contextlib import asynccontextmanager

from asset_microservice.config import rabbitmq_config
from aio_pika import connect
#from opentelemetry.instrumentation.aio_pika import AioPikaInstrumentor

@asynccontextmanager
async def rabbitmq_connection():
    connection = await connect(rabbitmq_config.url)
    async with connection:
        channel = await connection.channel()
        exchange = await channel.declare_exchange("crypto_prices", type="fanout")
        yield exchange