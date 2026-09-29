from contextlib import asynccontextmanager

from aio_pika import connect

from alert_microservice.config import rabbitmq_config


@asynccontextmanager
async def rabbitmq_connection():
    connection = await connect(rabbitmq_config.url)
    async with connection:
        channel = await connection.channel()
        crypto_exchange = await channel.declare_exchange("crypto_prices", type="fanout")
        trigger_exchange = await channel.declare_exchange("trigger", type="fanout")
        trigger_queue = await channel.declare_queue("trigger_queue")
        crypto_queue = await channel.declare_queue("crypto_queue")
        await trigger_queue.bind(trigger_exchange)
        await crypto_queue.bind(crypto_exchange)
        yield {"crypto_q": crypto_queue, "trigger_q": trigger_queue, "trigger_ex": trigger_exchange}


