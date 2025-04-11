import json
import uuid

from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey
from aiogram.types import CallbackQuery
from playhouse.shortcuts import model_to_dict

from src.api_aliexpress.request import request_api
from src.api_telegram import CacheKey, CacheKeyExtended, CacheKeyReview
from src.core import config
from src.database import orm


async def check_current_state(state: FSMContext, callback: CallbackQuery) -> bool:
    """

    :param state:
    :param callback:
    :return:
    """
    key = StorageKey(
        bot_id=callback.bot.id,
        chat_id=callback.message.chat.id,
        user_id=callback.from_user.id,
    )
    return bool(await state.storage.get_state(key))


class CacheKeyManager:
    @staticmethod
    async def generate_key(key, api_page, extra: str):
        """Получает ключ для поиска кэша."""
        return CacheKey(key=key, api_page=api_page, extra=extra).pack()

    @staticmethod
    async def generate_extra_key(data: CacheKeyExtended, extra: str | None = None):
        """Получает ключ для поиска кэша."""
        return CacheKeyExtended(
            key=data.key,
            api_page=data.api_page,
            sub_page=data.sub_page,
            extra=extra,
        ).pack()

    @staticmethod
    async def generate_review_key(data: CacheKeyExtended, extra: str):
        """Получает ключ для поиска кэша."""
        return CacheKeyReview(
            key=data.key, api_page=data.api_page, extra=extra, page=data.page
        ).pack()

    @staticmethod
    async def create_uuid_key(length: int) -> str:
        """

        :param length:
        :return:
        """
        return "{0:.10}".format(str(uuid.uuid4().hex)[:length])

    @staticmethod
    async def get_or_create_key(data):
        if data and await orm.query.get_from_db(data.key):
            return data.key, False
        else:
            new_key = await CacheKeyManager.create_uuid_key(6)
            return new_key, True


def counter_key(name, data):
    count = 0
    # max_len = 64
    # print('=' * 20)
    # print(name.upper().rjust(10, "_"))
    # print(f"[{max_len}] [{count}]")
    for i in str(data).split(":"):
        count += len(i)
        # print(f"[{max_len - count}] [{count}] {len(i)} - {i}")
    # print(f"{name.upper().rjust(10, '_')} TOTAL LEN = [{count}] SAVE RANGE = {max_len - count}")


async def get_query_from_db(key: str):
    params_from_db = await orm.query.get_from_db(key)
    saved_query_dict = json.loads(model_to_dict(params_from_db).get("query"))
    return dict(
        q=saved_query_dict.get("q", None),
        page=saved_query_dict.get("page", 1),
        sort=saved_query_dict.get("sort", None),
        startPrice=saved_query_dict.get("startPrice", None),
        endPrice=saved_query_dict.get("endPrice", None),
    )


async def previous_api_page(key, api_page):
    params = await get_query_from_db(key)
    params["url"] = config.URL_API_ITEM_LIST
    params["page"] = str(api_page)
    prev_list = await request_api(params)
    return prev_list
