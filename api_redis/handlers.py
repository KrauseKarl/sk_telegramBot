import json
from datetime import timedelta
from typing import Any

from redis import asyncio as aioredis

from api_telegram import ItemCBD, DetailCBD
from core import config, conf
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
            self.client = await aioredis.Redis(host=conf.redis_host)
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
        print(f"🔑  EXIST = {bool(value)}[{key}]")
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
        return state

    async def get_keys(self) -> list:
        """Get all keys from Redis."""
        if not self.client:
            await self.connect()
        keys = await self.client.keys()
        if keys:
            print("keys count = {0} {1}".format(
                len(keys),
                '\n'.join([f"\t\t\t🔑 {k}" for k in sorted(keys)]))
            )
        return keys

    async def get_from_cache(self, cache_key: str):
        return await self.get_data(cache_key)

    async def set_in_cache(self, cache_key: str, data: Any):
        data_list = await self.get_data(cache_key)
        if data_list is None:
            await self.set_data(key=cache_key, value=data)
