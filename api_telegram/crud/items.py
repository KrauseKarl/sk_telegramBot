import json
from typing import Any, Dict

from aiogram.fsm.context import FSMContext
from playhouse.shortcuts import model_to_dict
from api_aliexpress.request import request_api_fake, request_api
from api_redis.handlers import redis_get_data_from_cache, redis_set_data_to_cache, redis_get_keys
from api_telegram.callback_data import *
from api_telegram.statments import CacheFSM
from core import config
from database.paginator import *


async def get_data_from_cache(call_data: ItemCBD | DetailCBD):
    cache_key = CacheKey(key=call_data.key, api_page=call_data.api_page).pack()
    res = await redis_get_data_from_cache(cache_key)
    return res


async def set_data_to_cache(data, call_data: ItemCBD | DetailCBD):
    cache_key = CacheKey(key=call_data.key, api_page=call_data.api_page).pack()
    cache_data = await redis_get_data_from_cache(cache_key)
    if cache_data is None:
        await redis_set_data_to_cache(key=cache_key, value=data)


async def save_query_in_db(data: dict, key: str, page: str | int):
    data['page'] = str(page)
    query_str = json.dumps(data, ensure_ascii=False)
    save_query_dict = CacheDataModel(
        user=int(data['user_id']),
        key=str(key),
        query=str(query_str)
    ).model_dump()
    await orm_save_query_in_db(save_query_dict)


async def update_query_in_db(data: dict, key: str):
    query_str = json.dumps(data, ensure_ascii=False)
    update_query_dict = CacheDataUpdateModel(query=str(query_str)).model_dump()
    await orm_update_query_in_db(update_query_dict.get('query'), key)


async def create_cache_key(key: str, page: str, extra: str, sub_page: str = None):
    return CacheKey(
        key=key,
        api_page=int(page),
        extra=extra
    ).pack()


async def get_query_from_db(key: str, params: dict | None = None):
    params_from_db = await orm_get_query_from_db(key)
    saved_query_dict = json.loads(model_to_dict(params_from_db).get("query"))
    print('🚩 query - {0}'.format(saved_query_dict.values()))
    if params is None:
        params = dict()
    params['q'] = saved_query_dict.get('q', None)
    params['page'] = saved_query_dict.get('page', 1)
    params['sort'] = saved_query_dict.get('sort', None)
    params['startPrice'] = saved_query_dict.get('startPrice', None)
    params['endPrice'] = saved_query_dict.get('endPrice', None)

    return params


async def refresh_params_dict(params: dict, key: str):
    if params.get('q', None) is None:
        params = await get_query_from_db(key, params)
        print('#㊗️㊗️㊗️ >>>> GET PARAMS FROM DB ', '||'.join([f"{k} {v}" for k, v in params.items()]))
        return params

    print('#✅✅✅ >>>> GET PARAMS FROM STATE', '||'.join([f"{k} {v}" for k, v in params.items()]))
    return params


async def get_paginate_item(params: dict[str, Any], data: ItemCBD | DetailCBD):
    """

    :param params: FSMContext
    :param data: ItemCBD | DetailCBD Callback_Data
    :return: Paginator
    """
    params['url'] = config.URL_API_ITEM_LIST
    await redis_get_keys()
    print("♻️♻️♻️ DATA = {0}\n♻️♻️♻️ PARAMS = {1} [{2}]".format(data, params.get('q', None), params.get('page', None)))
    cache_key = await create_cache_key(data.key, data.api_page, 'list')
    item_list = await redis_get_data_from_cache(cache_key)
    page = int(data.page) if int(data.page) else 1
    if item_list is None:
        ########################################################################
        print('\n❌❌❌ #0 >>>> NO CACHE NEW REQUEST ')
        params = await refresh_params_dict(params, data.key)
        page = int(data.page)
        if data.api_page:
            params['page'] = data.api_page
        #######################################################################
        response = await request_api(params)
        item_list = response["result"]["resultList"]

        # todo `save_to_cache(data: dict, key: str)`############################
        is_cached = await redis_get_data_from_cache(cache_key)
        if not is_cached:
            print('SAVE IN ♻️CACHE♻️')
            await redis_set_data_to_cache(key=cache_key, value=item_list)
        # todo `save_to_cache(data: dict, key: str)`############################

        print('❌❌❌ #0 >>>> NO CACHE NEW REQUEST \n')

        ########################################################################
    if int(data.api_page) == 0 or page > len(item_list):
        params = await refresh_params_dict(params, data.key)
        page = 1
        if data.api_page:
            params['page'] = str(int(data.api_page) + 1)
        else:
            params['page'] = str(int(params['page']) + 1)
        response = await request_api(params)
        item_list = response["result"]["resultList"]
        cache_key = await create_cache_key(data.key, params['page'], 'list')

        # todo `save_to_cache(data: dict, key: str)`############################
        is_cached = await redis_get_data_from_cache(cache_key)
        if not is_cached:
            await redis_set_data_to_cache(key=cache_key, value=item_list)
        await update_query_in_db(params, data.key)
        # todo `save_to_cache(data: dict, key: str)`############################

    paginator = Paginator(array=item_list, page=page)
    item = paginator.get_page()[0]
    return dict(
        key=data.key,
        api_page=int(params['page']),
        page=str(page),
        item=item['item'],
        total_pages=paginator.len
    )
