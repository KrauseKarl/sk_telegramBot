from typing import Any, Dict

from aiogram.fsm.context import FSMContext

from api_aliexpress.request import request_api_fake, request_api
from api_redis.handlers import redis_get_data_from_cache, redis_set_data_to_cache
from api_telegram.callback_data import *
from api_telegram.statments import CacheFSM
from core import config
from database.pagination import *


async def get_data_from_cache(call_data: ItemCBD | DetailCBD):
    cache_key = CacheKey(key=call_data.key, api_page=call_data.api_page).pack()
    res = await redis_get_data_from_cache(cache_key)
    print(f"get_data_from_cache {res}")
    return res


async def set_data_to_cache(data, call_data: ItemCBD | DetailCBD):
    cache_key = CacheKey(key=call_data.key, api_page=call_data.api_page).pack()
    cache_data = await redis_get_data_from_cache(cache_key)
    if cache_data is None:
        await redis_set_data_to_cache(key=cache_key, value=data)


async def get_paginate_item(state_data: Dict[str, Any], callback_data: ItemCBD | DetailCBD):
    key = callback_data.key
    page = int(callback_data.page)
    api_page = int(callback_data.api_page)
    cache_key = CacheKey(key=key, api_page=api_page).pack()
    item_list_cache = await redis_get_data_from_cache(cache_key)

    print(f"⬜️DATA FROM 🟩 CACHE ")
    if api_page == 0 or page > len(item_list_cache):
        print(f"⬜️DATA FROM 🟥 REQUEST")
        api_page += 1
        ########################################################################
        if config.FAKE_MODE:
            result = await request_api_fake(page=api_page, query=state_data.get("product"))
        else:
            result = await request_api(
                query=state_data.get("product"),
                sort=state_data.get("sort"),
                start_price=state_data.get("price_min"),
                end_price=state_data.get("price_max"),
                url=config.URL_API_ITEM_LIST,
                page=str(api_page)
            )
        ########################################################################
        item_list_cache = result["result"]["resultList"]
        cache_key = CacheKey(key=key, api_page=api_page).pack()
        page = 1
        cache_data = await redis_get_data_from_cache(cache_key)
        if cache_data is None:
            await redis_set_data_to_cache(key=cache_key, value=item_list_cache)

    return Paginator(array=item_list_cache, page=page)


async def save_query_in_cache_state(state: FSMContext):
    data = await state.get_data()

    await state.set_state(CacheFSM.product)
    await state.update_data(product=data.get("product"))

    await state.set_state(CacheFSM.price_min)
    await state.update_data(price_min=data.get("price_min"))

    await state.set_state(CacheFSM.price_max)
    await state.update_data(price_max=data.get("price_max"))

    await state.set_state(CacheFSM.qnt)
    await state.update_data(qnt=data.get("qnt"))

    await state.set_state(CacheFSM.sort)
    await state.update_data(sort=data.get("sort"))

    data_in_cache = await state.get_data()

    await state.clear()

    return data_in_cache
