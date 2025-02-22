import inspect
import json
import os

import httpx

from core import config
from core.config import conf
from database.exceptions import *


async def save_data_json(data, page: str = None, query: str = None, item_id: str = None):

    try:
        file_name = "{0}_{1}.json".format(query.replace(' ', "_").lower(), page)
        file_path = os.path.join(
            config.BASE_DIR,
            "_json_example",
            "_real_data",
            file_name
        )
        with open(file_path, "w") as file:
            json.dump(data, file, ensure_ascii=False, indent=4)
    except AttributeError:
        file_name = "{0}.json".format(item_id)
        file_path = os.path.join(
            config.BASE_DIR,
            "_json_example",
            "_favorite",
            file_name
        )
        with open(file_path, "w") as file:
            json.dump(data, file, ensure_ascii=False, indent=4)


async def request_api_fake(page: str | int, query: str = None):
    try:
        file_name = "{0}_{1}.json".format(query.replace(" ", "_").lower(), page)
        path = os.path.join(config.BASE_DIR, "_json_example", "_real_data", file_name)
        print(f"{path= }")
        with open(path, 'r') as file:
            data = json.load(file)
        return data
    except FileNotFoundError:
        path = os.path.join(config.BASE_DIR, "_json_example", "_fake", "list_{0}.json".format(page))
        with open(path, 'r') as file:
            data = json.load(file)
        return data
        # raise CustomError('⚠️ JSON file not found.')


async def request_api(
        url: str = None,
        page: str = None,
        item_id: str = None,
        query: str = None,
        sort: str = None,
        cat_id: str = None,
        start_price: str = None,
        end_price: str = None,

) -> dict:
    full_url = "/".join([conf.base_url, url])
    if query:
        conf.querystring["q"] = query
    if item_id:
        conf.querystring["itemId"] = item_id
    if sort:
        conf.querystring["sort"] = sort
    if cat_id:
        conf.querystring["catId"] = str(cat_id)
    if start_price:
        conf.querystring["startPrice"] = start_price
    if end_price:
        conf.querystring["endPrice"] = end_price
    if page:
        conf.querystring["page"] = page

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                url=full_url,
                headers=conf.headers,
                params=conf.querystring
            )
        result = response.json()

        ##################################################################
        # todo delete after develop
        print("☀️☀️☀️☀️☀️REQUEST TO ALIEXPRESS API - {}".format(conf.querystring.items()))

        if page and query:
            await save_data_json(data=result, query=query, page=page)
        if item_id:
            await save_data_json(data=result, item_id=item_id)
        # todo delete after develop
        ##################################################################

    except httpx.ReadTimeout as error:
        raise FreeAPIExceededError(
            message="⚠️ HTTP ERROR\n{0}".format(error)
        )

    if "message" in result:
        print(f"❌ лимит API превышен")
        raise FreeAPIExceededError(
            message="⚠️ лимит API превышен\n{0}".format(
                result.get('message')
            )
        )
    return result

# async def request_item_list(url: str, q=None, sort=None, cat_id=None) -> dict:
#     full_url = "/".join([conf.base_url, url])
#     print(full_url)
#     if q and sort:
#         conf.querystring["q"] = q
#         conf.querystring["sort"] = sort
#     async with httpx.AsyncClient() as client:
#         response = await client.get(
#             url=full_url,
#             headers=conf.headers,
#             params=conf.querystring)
#     return response.json()
#
#
# async def request_item_detail(item_id: str) -> dict:
#     url = config.URL_API_ITEM_DETAIL
#     base_url = conf.base_url
#     full_url = base_url + "/" + url
#     conf.querystring["itemId"] = item_id
#     async with httpx.AsyncClient() as client:
#         response = await client.get(
#             url=full_url,
#             headers=conf.headers,
#             params=conf.querystring)
#     result = response.json()
#     print(f"{'message' in result= }")
#     if "message" in result:
#         raise FreeAPIExceededError(
#             message="❌ лимит API превышен\n{0}".format(
#                 result.get('message')
#             )
#         )
#     return response.json()
