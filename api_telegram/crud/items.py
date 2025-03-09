from typing import Any


from playhouse.shortcuts import model_to_dict
from api_aliexpress.request import *
from api_redis.handlers import *
from api_telegram.callback_data import *
from api_telegram.statments import CacheFSM
from core import config
from database.exceptions import *
from database.paginator import *
from database.pydantic import *

redis_handler = RedisHandler()


async def get_data_from_cache(call_data: ItemCBD | DetailCBD, extra: str | None = None):
    cache_key = CacheKey(
        key=call_data.key,
        api_page=call_data.api_page,
        extra=extra
    ).pack()
    data_list = await redis_handler.get_data(cache_key)
    # data_list = await redis_get_data_from_cache(cache_key)
    if data_list:
        print('DATA ♻️♻️♻️♻️♻️♻️♻️♻️♻️♻️♻️♻️♻️♻️ FROM CACHE')
    return data_list


async def set_data_in_cache(data, call_data: ItemCBD | DetailCBD, extra: str | None = None):
    cache_key = CacheKey(
        key=call_data.key,
        api_page=call_data.api_page,
        extra=extra
    ).pack()
    data_list = await redis_handler.get_data(cache_key)
    # cache_data = await redis_get_data_from_cache(cache_key)
    if data_list is None:
        # await redis_set_data_to_cache(key=cache_key, value=data)
        await redis_handler.set_data(key=cache_key, value=data)


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
        print('㊗️ >>>> GET PARAMS FROM DB')
        return params
    return params


async def get_item(data_list: list, page: str | int):
    paginator = Paginator(array=data_list, page=page)
    return paginator.get_page()[0]


async def get_paginator_len(data_list: list, page: str | int):
    paginator = Paginator(array=data_list, page=page)
    return paginator.len


async def get_data_by_request_to_api(params: dict):
    response = await request_api(params)

    try:
        if params.get('q'):
            return response["result"]["resultList"]
        else:
            return response
    except KeyError:
        if "message" in response:
            raise FreeAPIExceededError(
                message="⚠️HTTP error\n{0}".format(
                    response.get('message')
                )
            )


# async def get_paginate_item(params: dict[str, Any], data: ItemCBD | DetailCBD):
#     """
#
#     :param params: FSMContext
#     :param data: ItemCBD | DetailCBD Callback_Data
#     :return: Paginator
#     """
#     params['url'] = config.URL_API_ITEM_LIST
#     print("♻️ DATA = {0}\n♻️ PARAMS = {1} [{2}]".format(
#         data, params.get('q', None),
#         params.get('page', None)
#     ))
#     # cache_key = await create_cache_key(data.key, data.api_page, 'list')
#     # item_list = await redis_get_data_from_cache(cache_key)
#     item_list = await get_data_from_cache(data, extra="list")
#     page = int(data.page) if int(data.page) else 1
#     if item_list is None:
#         ########################################################################
#         print('\n❌>>>> NO CACHE NEW REQUEST ')
#         params = await refresh_params_dict(params, data.key)
#         page = int(data.page)
#         if data.api_page:
#             params['page'] = data.api_page
#         #######################################################################
#         response = await request_api(params)
#         item_list = response["result"]["resultList"]
#
#         # todo `save_to_cache(data: dict, key: str)`############################
#         # is_cached = await redis_get_data_from_cache(cache_key)
#         # if not is_cached:
#         #     print('SAVE IN ♻️CACHE♻️')
#         #     await redis_set_data_to_cache(key=cache_key, value=item_list)
#         await set_data_to_cache(item_list, data, extra='list')
#         # todo `save_to_cache(data: dict, key: str)`############################
#         ########################################################################
#     if int(data.api_page) == 0 or page > len(item_list):
#         params = await refresh_params_dict(params, data.key)
#         page = 1
#         api_page = data.api_page if data.api_page else params['page']
#         params['page'] = str(int(api_page) + 1)
#         response = await request_api(params)
#         item_list = response["result"]["resultList"]
#         # cache_key = await create_cache_key(data.key, params['page'], 'list')
#         # todo `save_to_cache(data: dict, key: str)`############################
#         await set_data_to_cache(item_list, data, extra='list')
#         # is_cached = await redis_get_data_from_cache(cache_key)
#         # if not is_cached:
#         #     await redis_set_data_to_cache(key=cache_key, value=item_list)
#         # await update_query_in_db(params, data.key)
#         # todo `save_to_cache(data: dict, key: str)`############################
#
#     item = await get_item(item_list, page)
#
#     return dict(
#         key=data.key,
#         api_page=int(params['page']),
#         page=str(page),
#         item=item['item'],
#         total_pages=await get_paginator_len(item_list, page)
#     )
async def get_paginate_item(params: dict[str, Any], data: ItemCBD | DetailCBD):
    """

    :param params: FSMContext
    :param data: ItemCBD | DetailCBD Callback_Data
    :return: Paginator
    """
    params['url'] = config.URL_API_ITEM_LIST
    item_list = await get_data_from_cache(data, extra="list")
    page = int(data.page) if int(data.page) else 1

    if item_list is None:
        page = int(data.page)
        params = await refresh_params_dict(params, data.key)
        if data.api_page:
            params['page'] = data.api_page
        item_list = await get_data_by_request_to_api(params)
        await update_query_in_db(params, data.key)
        await set_data_in_cache(item_list, data, extra='list')

    if int(data.api_page) == 0 or page > len(item_list):
        page = 1
        params = await refresh_params_dict(params, data.key)
        api_page = data.api_page if data.api_page else params['page']
        params['page'] = str(int(api_page) + 1)
        item_list = await get_data_by_request_to_api(params)
        await update_query_in_db(params, data.key)
        await set_data_in_cache(item_list, data, extra='list')


    item = await get_item(item_list, page)

    return {
        "key": data.key,
        "api_page": int(params['page']),
        "page": str(page),
        "item": item['item'],
        "total_pages": await get_paginator_len(item_list, page)
    }
