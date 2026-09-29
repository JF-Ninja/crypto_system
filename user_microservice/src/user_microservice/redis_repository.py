

class RedisRepository:

    def __init__(self, redis):
        self.db = redis

    async def set_pairs(self, ttl: int = None, **kwargs):
        for key, value in kwargs.items():
            await self.db.set(name=key, value=value, ex=ttl)

    async def get_pairs(self, *args):
        values = await self.db.mget(*args)
        return dict(zip(args, values))

    async def get_all_pairs(self):
        keys = await self.db.keys("*")
        values = await self.db.mget(*keys)
        return dict(zip(keys, values))

    async def delete_pairs(self, *args):
        return await self.db.delete(*args)