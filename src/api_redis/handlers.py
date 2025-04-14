import json
from datetime import timedelta
from typing import Any

from redis import asyncio as aioredis

from src.core import conf, config
from src.database.exceptions import CustomError
from src.logger import logger as log


class RedisHandler:
    """Класс для обработки операций Redis."""

    def __init__(self):
        self.client = None

    async def connect(self) -> aioredis.Redis:
        """Установка соединение с Redis."""
        try:
            self.client = await aioredis.Redis(host=conf.redis_host)
            ping = await self.client.ping()
            if ping is True:
                return self.client
        except aioredis.ConnectionError:
            msg = "❌📶 REDIS не может установить связь."
            log.error_log.error(msg)
            raise CustomError(message=msg)

    async def flush_keys(self) -> None:
        """Удаляет все ключи из Redis."""
        if not self.client:
            await self.connect()
        keys = await self.client.keys()
        log.info_log.debug(f"REDIS🔑 {sorted(keys)}")
        await self.client.flushall()
        log.info_log.debug("REDIS🚫 keys deleted")
        keys = await self.client.keys()
        log.info_log.debug(f"REDIS🔑 {sorted(keys)}")

    async def get_data(self, key: str):
        """Получает данные из Redis по ключу."""
        if not self.client:
            await self.connect()

        value = await self.client.get(key)
        log.info_log.debug(f"REDIS🔑 EXIST = {bool(value)}[{key}]")
        return json.loads(value) if value else None

    async def set_data(self, key: str, value: str | dict) -> bool:
        """Записывает данные в Redis с истечением срока действия."""
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
        """Получает все ключи от Redis."""
        if not self.client:
            await self.connect()
        keys = await self.client.keys()
        if keys:
            log.info_log.debug(
                "REDIS keys count = {0} {1}".format(
                    len(keys),
                    "\n".join([f"REDIS 🔑 {k}" for k in sorted(keys)]),
                )
            )
        return keys

    async def get_from_cache(self, cache_key: str):
        """Получает кэш из Redis."""
        return await self.get_data(cache_key)

    async def set_in_cache(self, cache_key: str, data: Any):
        """Записывает кэш в Redis."""
        data_list = await self.get_data(cache_key)
        if data_list is None:
            await self.set_data(key=cache_key, value=data)
