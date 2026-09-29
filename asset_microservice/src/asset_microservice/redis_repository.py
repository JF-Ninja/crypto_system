

class RedisRepository:

    def __init__(self, redis):
        self.db = redis

    async def set_pairs(self, ttl: int = None, **kwargs):
        for key, value in kwargs.items():
            await self.db.set(name=key, value=value, ex=ttl)

    async def set_hash_pairs(self, hash_key: str, **kwargs):
        await self.db.hset(hash_key, mapping=kwargs)

    async def get_pairs(self, *args):
        if args:
            values = await self.db.mget(*args)
            return dict(zip(args, values))
        keys = await self.db.keys("*")
        values = await self.db.mget(*keys)
        return dict(zip(keys, values))

    async def get_hash_pairs(self, hash_key: str, *args):
        if args:
            values = await self.db.hmget(hash_key, *args)
            return dict(zip(args, values))
        dict_pairs = await self.db.hgetall(hash_key)
        return dict_pairs


    async def delete_pairs(self, *args):
        return await self.db.delete(*args)

    async def delete_hash_pairs(self, hash_key: str, *args):
        return await self.db.hdel(hash_key, *args)
