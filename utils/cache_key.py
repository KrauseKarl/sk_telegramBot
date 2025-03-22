import json
import uuid

from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey
from aiogram.types import CallbackQuery
from playhouse.shortcuts import model_to_dict

from api_aliexpress.request import request_api
from api_telegram.callback_data import CacheKeyExtended
from core import config
from database.orm import orm_get_query_from_db


async def check_current_state(
        state: FSMContext,
        callback: CallbackQuery
) -> bool:
    """

    :param state:
    :param callback:
    :return:
    """
    key = StorageKey(
        bot_id=callback.bot.id,
        chat_id=callback.message.chat.id,
        user_id=callback.from_user.id
    )
    return bool(await state.storage.get_state(key))


async def create_uuid_key(length: int) -> str:
    """

    :param length:
    :return:
    """
    return "{0:.10}".format(str(uuid.uuid4().hex)[:length])


async def get_or_create_key(data, user_id):
    if data and await orm_get_query_from_db(data.key):
        return data.key, False
    # elif await orm_get_query_by_id_from_db(user_id):
    #     return await orm_get_query_by_id_from_db(user_id)
    else:
        new_key = await create_uuid_key(6)
        print(f'🔑🔑🔑 NEW KEY {new_key}')
        return new_key, True


async def get_extra_cache_key(data: CacheKeyExtended, extra: str | None = None):
    return CacheKeyExtended(
        key=data.key,
        api_page=data.api_page,
        sub_page=data.sub_page,
        extra=extra
    ).pack()


def counter_key(name, data):
    count = 0
    max_len = 64
    # print('=' * 20)
    # print(name.upper().rjust(10, "_"))
    # print(f"[{max_len}] [{count}]")
    for i in str(data).split(':'):
        count += len(i)
        # print(f"[{max_len - count}] [{count}] {len(i)} - {i}")
    # print(f"{name.upper().rjust(10, '_')} TOTAL LEN = [{count}] SAVE RANGE = {max_len - count}")


async def get_query_from_db(key: str, params: dict | None = None):
    params_from_db = await orm_get_query_from_db(key)
    saved_query_dict = json.loads(model_to_dict(params_from_db).get("query"))
    if params is None:
        params = dict()
    params['q'] = saved_query_dict.get('q', None)
    params['page'] = saved_query_dict.get('page', 1)
    params['sort'] = saved_query_dict.get('sort', None)
    params['startPrice'] = saved_query_dict.get('startPrice', None)
    params['endPrice'] = saved_query_dict.get('endPrice', None)

    return params
async def previous_api_page(key, api_page):
    params = dict(url=config.URL_API_ITEM_LIST)
    params = await get_query_from_db(key, params)
    params['page'] = str(api_page)
    prev_list = await request_api(params)

    return len(prev_list)
