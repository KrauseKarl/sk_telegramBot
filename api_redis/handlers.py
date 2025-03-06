import json
from datetime import timedelta

from redis import asyncio as aioredis

from core import config
from database.exceptions import CustomError


import json
from datetime import timedelta
from redis import asyncio as aioredis
from core import config
from database.exceptions import CustomError


class RedisHandler:
    """A class to handle Redis operations."""

    def __init__(self):
        self.client = None

    async def connect(self) -> aioredis.Redis:
        """Establish a connection to Redis."""
        try:
            self.client = await aioredis.Redis()
            ping = await self.client.ping()
            if ping is True:
                return self.client
        except aioredis.ConnectionError:
            raise CustomError('❌📶 REDIS не может установить связь.')

    async def flush_keys(self) -> None:
        """Flush all keys from Redis."""
        if not self.client:
            await self.connect()

        keys = await self.client.keys()
        print(f"🔑 {sorted(keys)}")

        await self.client.flushall()
        print("🚫 Redis keys deleted")

        keys = await self.client.keys()
        print(f"🔑 {sorted(keys)}")

    async def get_data(self, key: str):
        """Get data from Redis by key."""
        if not self.client:
            await self.connect()

        value = await self.client.get(key)
        return json.loads(value) if value else None

    async def set_data(self, key: str, value: str | dict) -> bool:
        """Set data to Redis with an expiration time."""
        if not self.client:
            await self.connect()

        value = json.dumps(value, ensure_ascii=False, indent=4)
        state = await self.client.setex(
            key,
            timedelta(seconds=config.CACHE_LIVE_TIME),
            value=value,
        )

        keys = await self.client.keys()
        if keys:
            print('\n'.join([f"🔑🔑🔑 {k}" for k in sorted(keys)]))

        return state

    async def get_keys(self) -> list:
        """Get all keys from Redis."""
        if not self.client:
            await self.connect()

        keys = await self.client.keys()
        if keys:
            print("keys count = {0} {1}".format(
                len(keys),
                '\n'.join([f"🔑 {k}" for k in sorted(keys)]))
            )
        return keys

#
# async def redis_connect() -> aioredis.Redis:
#     """Get connect with redis."""
#     try:
#         client = await aioredis.Redis()
#         ping = await client.ping()
#         if ping is True:
#             return client
#     except aioredis.client.ConnectionError:
#         raise CustomError('❌📶 REDIS не может установить связь.')
#
#
# async def redis_flush_keys() -> aioredis.Redis:
#     """Flush all keys  from redis."""
#     client = await redis_connect()
#
#     keys = await client.keys()
#     print(f"🔑{sorted(keys)}")
#
#     await client.flushall()
#     print("🚫 Redis keys deleted")
#
#     keys = await client.keys()
#     print(f"🔑{sorted(keys)}")
#
#     return client
#
#
# async def redis_get_data_from_cache(key: str):
#     """Get data from redis."""
#     try:
#         client = await redis_connect()
#         value = await client.get(key)
#         return json.loads(value)
#     except TypeError:
#         return None
#
#
# async def redis_set_data_to_cache(key: str, value: str) -> bool:
#     """Set data to redis."""
#     client = await redis_connect()
#     value = json.dumps(value, ensure_ascii=False, indent=4)
#     state = await client.setex(
#         key,
#         timedelta(seconds=config.CACHE_LIVE_TIME),
#         value=value,
#     )
#     keys = await client.keys()
#     if keys:
#         print('\n'.join([f"🔑🔑🔑 {k}" for k in sorted(keys)]))
#     return state
#
#
# async def redis_get_keys() -> aioredis.Redis:
#     """Get all keys  from redis."""
#     client = await redis_connect()
#     keys = await client.keys()
#     if keys:
#         print("keys count = {0} {1}".format(
#             len(keys),
#             '\n'.join([f"🔑 {k}" for k in sorted(keys)]))
#         )
#     return client
