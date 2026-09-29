


class RedisRepository:

    def __init__(self, redis):
        self.redis = redis

    async def set_pairs(self, ttl: int = None, **kwargs):
        for key, value in kwargs.items():
            await self.redis.set(name=key, value=value, ex=ttl)

    async def get_pairs(self, *args):
        if args:
            values = await self.redis.mget(*args)
            return dict(zip(args, values))
        keys = await self.redis.keys("*")
        values = await self.redis.mget(*keys)
        return dict(zip(keys, values))

    async def delete_pairs(self, *args):
        return await self.redis.delete(*args)

    async def set_hash_pairs(self, hash_key: str, **kwargs):
        await self.redis.hset(hash_key, mapping=kwargs)

    async def get_hash_pairs(self, hash_key: str, *args):
        if args:
            values = await self.redis.hmget(hash_key, *args)
            return dict(zip(args, values))
        dict_pairs = await self.redis.hgetall(hash_key)
        return dict_pairs

    async def delete_hash_pairs(self, hash_key: str, *args):
        return await self.redis.hdel(hash_key, *args)