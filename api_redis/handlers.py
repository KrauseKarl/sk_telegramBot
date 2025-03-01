import json
from datetime import timedelta

from redis import asyncio as aioredis

from core import config
from database.exceptions import CustomError


async def redis_connect() -> aioredis.Redis:
    """Get connect with redis."""
    try:
        client = await aioredis.Redis()
        ping = await client.ping()
        if ping is True:
            return client
    except aioredis.client.ConnectionError:
        raise CustomError('❌📶 REDIS не может установить связь.')


async def redis_flush_keys() -> aioredis.Redis:
    """Flush all keys  from redis."""
    client = await redis_connect()

    keys = await client.keys()
    print(f"🔑{sorted(keys)}")

    await client.flushall()
    print("🚫 Redis keys deleted")

    keys = await client.keys()
    print(f"🔑{sorted(keys)}")

    return client


async def redis_get_data_from_cache(key: str):
    """Get data from redis."""
    try:
        client = await redis_connect()
        value = await client.get(key)
        # if value is None:
        #     raise CustomError('❌ Redis can not find data with that `key`')
        return json.loads(value)
    except TypeError:
        return None


async def redis_set_data_to_cache(key: str, value: str) -> bool:
    """Set data to redis."""
    client = await redis_connect()
    value = json.dumps(value, ensure_ascii=False, indent=4)
    state = await client.setex(
        key,
        timedelta(seconds=config.CACHE_LIVE_TIME),
        value=value,
    )
    keys = await client.keys()
    if keys:
        print('\n'.join([f"🟧 {k}" for k in sorted(keys)]))
    return state


async def redis_get_keys() -> aioredis.Redis:
    """Flush all keys  from redis."""
    client = await redis_connect()
    keys = await client.keys()
    if keys:
        print('\n'.join([f"🔑 {k}" for k in sorted(keys)]))

    return client
