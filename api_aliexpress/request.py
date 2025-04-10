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

PREFIX_FOLDER = {
    "list": ITEM_LIST_FAKE_FOLDER,
    "detail": DETAIL_FAKE_FOLDER,
    "review": REVIEW_FAKE_FOLDER,
    "error": "_fake"
}


async def save_fake_data(result: dict, params: dict):
    # Определяем конфигурацию для каждого типа URL
    URL_CONFIG = {
        config.URL_API_ITEM_LIST: {
            "prefix": None,
            "folder": ITEM_LIST_FAKE_FOLDER,
            "args": {"query": params.get("query"), "page": params.get("page")}
        },
        config.URL_API_ITEM_DETAIL: {
            "prefix": "detail",
            "folder": DETAIL_FAKE_FOLDER,
            "args": {"item_id": params.get("itemId")}
        },
        config.URL_API_REVIEW: {
            "prefix": "review",
            "folder": REVIEW_FAKE_FOLDER,
            "args": {"item_id": params.get("itemId")}
        }
    }

    # Получаем конфигурацию для текущего URL
    config_data = URL_CONFIG.get(params.get("url"))

    if config_data:
        # Если есть префикс, проверяем существование файла
        if config_data["prefix"]:
            my_file = await get_path_to_json(
                prefix=config_data["prefix"],
                data=params.get("itemId")
            )
            if my_file.is_file():
                print(f"File {my_file} already exists for {params.get('url')}")
                return

        # Сохраняем данные
        await save_data_json(
            data=result,
            folder=config_data["folder"],
            config_data=config_data["args"]
        )
        print(f"Saved in /{config_data['folder']}")


async def save_data_json(data, config_data, folder: str = None, ):
    page = config_data.get('page')
    query = config_data.get('query')
    item_id = config_data.get('itemId')

    try:
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


#####################################################################################
async def get_path_to_json(prefix, data: str | tuple):
    if isinstance(data, tuple):
        file_name = "{0}_{1}.json".format(
            data[0].replace(" ", "_").lower(),
            data[1]
        )
    else:
        file_name = "{0}_{1}.json".format(prefix, data)
    return Path(
        os.path.join(
            config.BASE_DIR,
            FAKE_MAIN_FOLDER,
            PREFIX_FOLDER[prefix],
            file_name
        )
    )


#####################################################################################
async def request_api_fake(params):
    if params.get('itemId'):
        prefix = 'detail'
        path = await get_path_to_json(
            prefix, params.get('itemId')
        )
    elif params.get('filters'):
        prefix = 'review'
        path = await get_path_to_json(
            prefix, params.get('itemId')
        )
    else:
        prefix = 'list'
        path = await get_path_to_json(
            prefix, (params.get('q'), params.get('page'))
        )
    try:
        with open(path, 'r') as file:
            data = json.load(file)
    except FileNotFoundError:
        path = await get_path_to_json(
            "error", (prefix, 1)
        )
        with open(path, 'r') as file:
            data = json.load(file)
    finally:
        return data


async def request_api(params) -> dict:
    for key, value in params.items():
        if value:
            conf.querystring[key] = value
    print("\n▶️▶️▶️ REQUEST API {0}\n".format(params))
    if config.FAKE_MODE:
        result = await request_api_fake(params)
    else:
        try:
            timeout = httpx.Timeout(10.0, read=None)
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    url="/".join([conf.base_url, params.get("url")]),
                    headers=conf.headers,
                    params=conf.querystring,
                    timeout=timeout
                )
        except httpx.HTTPError as error:
            raise FreeAPIExceededError(
                message="⚠️ HTTP ERROR\n{0}".format(error)
            )
        result = response.json()
        if "message" in result:
            print(f"❌ лимит API превышен")
            raise FreeAPIExceededError(
                message="⚠️ лимит API превышен\n{0}".format(
                    result.get('message')
                )
            )
        # todo delete after develop #########################################
        await save_fake_data(result, params)
        # todo delete after develop #########################################

    return result


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


async def request_api_review(data) -> dict:
    json_file = await get_path_to_json('review', data.get("url"))
    if config.FAKE_MODE and json_file.is_file():

        print(f"🟩  DATA FROM 💾CACHE [REVIEW]".rjust(20, "🟩"))

        with open(json_file, 'r') as file:
            response = json.load(file)
    else:
        print(f"🟥 DATA FROM 🌐INTERNET [REVIEW]".rjust(20, "🟥"))

        for key, value in data.items():
            if value:
                conf.querystring[key] = value
        async with httpx.AsyncClient() as client:
            response = await client.get(
                url="/".join([conf.base_url, data.get("url")]),
                headers=conf.headers,
                params=conf.querystring
            )
    result = response.json()
    await save_data_json(data=result, config_data=data, folder=REVIEW_FAKE_FOLDER)
    return result


async def get_data_by_request_to_api(params: dict):
    response = await request_api(params)
    try:
        if params.get('q'):
            return response["result"]["resultList"]
        else:
            return response
    except KeyError:
        if "message" in response:
            print(response)
            raise FreeAPIExceededError(
                message="⚠️HTTP error\n{0}".format(
                    response.get('message')
                )
            )
