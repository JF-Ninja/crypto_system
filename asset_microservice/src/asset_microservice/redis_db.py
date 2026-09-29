from redis import asyncio as aioredis

from asset_microservice.config import redis_config

r = aioredis.Redis(
    host=redis_config.host,
    port=redis_config.port,
    password=redis_config.password,
    decode_responses=True
)