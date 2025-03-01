import inspect
import json
import os
from pathlib import Path

import httpx

from core import config
from core.config import conf
from database.exceptions import *

FAKE_MAIN_FOLDER = "_json_example"
DETAIL_FAKE_FOLDER = "_detail_view"
ITEM_LIST_FAKE_FOLDER = "_real_data"
REVIEW_FAKE_FOLDER = "_reviews"


async def save_data_json(
    data,
    page: str | int = None,
    query: str = None,
    item_id: int | str = None,
    folder: str = None
):
    try:
        print(f"{folder=}")
        folder_path = os.path.join(config.BASE_DIR, FAKE_MAIN_FOLDER, folder)
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)

        if item_id and folder == DETAIL_FAKE_FOLDER:
            file_name = "detail_{0}.json".format(item_id)

        elif item_id and folder == REVIEW_FAKE_FOLDER:
            file_name = "review_{0}.json".format(item_id)

        else:
            file_name = "{0}_{1}.json".format(
                query.replace(' ', "_").lower(),
                page
            )

        file_path = os.path.join(folder_path, file_name)
        with open(file_path, "w") as file:
            json.dump(data, file, ensure_ascii=False, indent=4)

    except AttributeError:
        file_name = "{0}.json".format(item_id)
        file_path = os.path.join(
            config.BASE_DIR,
            FAKE_MAIN_FOLDER,
            "_favorite",
            file_name
        )
        with open(file_path, "w") as file:
            json.dump(data, file, ensure_ascii=False, indent=4)


async def request_api_fake(page: str | int, query: str = None):
    try:
        file_name = "{0}_{1}.json".format(
            query.replace(" ", "_").lower(),
            page
        )
        path = os.path.join(
            config.BASE_DIR,
            FAKE_MAIN_FOLDER,
            ITEM_LIST_FAKE_FOLDER,
            file_name
        )
        print(f"{path= }")
        with open(path, 'r') as file:
            data = json.load(file)
        return data
    except FileNotFoundError:
        path = os.path.join(config.BASE_DIR, FAKE_MAIN_FOLDER, "_fake", "list_{0}.json".format(page))
        with open(path, 'r') as file:
            data = json.load(file)
        return data
        # raise CustomError('⚠️ JSON file not found.')


async def request_api_detail_fake(item_id: str | int):
    file_name = "detail_{0}.json".format(item_id)
    path = os.path.join(config.BASE_DIR, FAKE_MAIN_FOLDER, DETAIL_FAKE_FOLDER, file_name)
    with open(path, 'r') as file:
        data = json.load(file)
    return data


async def request_api_fake_favorite(itemid, query: str = 'футболка_мужская', page=1):
    file_name = "{0}_{1}.json".format(
        query.replace(" ", "_").lower(),
        page
    )
    path = os.path.join(
        config.BASE_DIR,
        FAKE_MAIN_FOLDER,
        ITEM_LIST_FAKE_FOLDER,
        file_name
    )
    response = dict()
    response["result"] = dict()
    with open(path, 'r') as file:
        data = json.load(file)
    for i in data["result"]["resultList"]:
        if str(i['item']['itemId']) == str(itemid):
            response["result"] = i
            return response


async def request_api_review_fake(item_id: str = None):
    file_name = "review_{0}.json".format(item_id)
    path = os.path.join(
        config.BASE_DIR,
        FAKE_MAIN_FOLDER,
        REVIEW_FAKE_FOLDER,
        file_name
    )
    with open(path, 'r') as file:
        data = json.load(file)
    return data


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
        print(f"$$$ {url = }")
        if url == config.URL_API_ITEM_LIST:
            await save_data_json(data=result, query=query, page=page, folder=ITEM_LIST_FAKE_FOLDER)
            print(f'save in /{ITEM_LIST_FAKE_FOLDER}')

        elif url == config.URL_API_ITEM_DETAIL:
            path = os.path.join(
                config.BASE_DIR,
                FAKE_MAIN_FOLDER,
                DETAIL_FAKE_FOLDER,
                "detail_{0}.json".format(item_id)
            )
            my_file = Path(path)
            print('****', my_file.is_file())
            # if not my_file.exists():
            if not my_file.is_file():
                await save_data_json(data=result, item_id=item_id, folder=DETAIL_FAKE_FOLDER)
                print(f'save in /{DETAIL_FAKE_FOLDER}')
            if not my_file.exists():
                await save_data_json(data=result, item_id=item_id, folder=DETAIL_FAKE_FOLDER)
                print(f'save in /{DETAIL_FAKE_FOLDER}')

        elif url == config.URL_API_REVIEW:
            path = os.path.join(
                config.BASE_DIR,
                FAKE_MAIN_FOLDER,
                DETAIL_FAKE_FOLDER,
                "review_{0}.json".format(item_id)
            )
            my_file = Path(path)
            if not my_file.is_file():
                await save_data_json(data=result, item_id=item_id, folder=REVIEW_FAKE_FOLDER)
                print(f'save in /{DETAIL_FAKE_FOLDER}')
            if not my_file.exists():
                await save_data_json(data=result, item_id=item_id, folder=REVIEW_FAKE_FOLDER)
                print(f'save in /{DETAIL_FAKE_FOLDER}')

            print(f'save in /{REVIEW_FAKE_FOLDER}')
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
