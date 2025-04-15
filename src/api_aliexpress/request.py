import httpx

from src.core.config import conf
from src.database import exceptions
from src.logger import logger as log


async def request_api(params) -> dict:
    """
    Функция делает запрос к внешнему API.

    Возвращает словарь response.
    :param params - словарь с параметрами запроса.
    :return response-словарь.
    """
    for key, value in params.items():
        if value:
            conf.querystring[key] = value
    msg = "▶️▶️▶️ REQUEST API {0}".format(params)
    log.info_log.info(msg)
    try:
        timeout = httpx.Timeout(10.0, read=None)
        async with httpx.AsyncClient() as client:
            response = await client.get(
                url="/".join([conf.base_url, params.get("url")]),
                headers=conf.headers,
                params=conf.querystring,
                timeout=timeout,
            )
    except httpx.HTTPError as error:
        msg = "⚠️ HTTP ERROR\n{0}".format(error)
        log.error_log.exception(msg)
        raise exceptions.FreeAPIExceededError(msg)
    result = response.json()
    if "message" in result:
        msg = "⚠️ request error\n{0}".format(result.get("message"))
        log.error_log.error(msg)
        raise exceptions.FreeAPIExceededError(message=msg)
    return result


async def get_data_by_request_to_api(params: dict):
    """
    Функция делает запрос к внешнему API.

    Возвращает значение по ключу `resultList`,
    если в запросе есть параметр `q`.
    Или возвращает весь словарь response.
    """
    response = await request_api(params)
    try:
        if params.get("q"):
            return response["result"]["resultList"]
        else:
            return response
    except KeyError:
        if "message" in response:
            msg = "⚠️HTTP error\n{0}".format(response.get("message"))
            log.error_log.error(msg)
            raise exceptions.FreeAPIExceededError(message=msg)


# import json
# import os
# from pathlib import Path
# from src.core import config
# FAKE_MAIN_FOLDER = "_json_example"
# DETAIL_FAKE_FOLDER = "_detail_view"
# ITEM_LIST_FAKE_FOLDER = "_real_data"
# REVIEW_FAKE_FOLDER = "_reviews"
#
# PREFIX_FOLDER = {
#     "list": ITEM_LIST_FAKE_FOLDER,
#     "detail": DETAIL_FAKE_FOLDER,
#     "review": REVIEW_FAKE_FOLDER,
#     "error": "_fake",
# }
#
#
# async def save_fake_data(result: dict, params: dict):
#     # Определяем конфигурацию для каждого типа URL
#     URL_CONFIG = {
#         config.URL_API_ITEM_LIST: {
#             "prefix": None,
#             "folder": ITEM_LIST_FAKE_FOLDER,
#             "args": {"query": params.get("query"), "page": params.get("page")},
#         },
#         config.URL_API_ITEM_DETAIL: {
#             "prefix": "detail",
#             "folder": DETAIL_FAKE_FOLDER,
#             "args": {"item_id": params.get("itemId")},
#         },
#         config.URL_API_REVIEW: {
#             "prefix": "review",
#             "folder": REVIEW_FAKE_FOLDER,
#             "args": {"item_id": params.get("itemId")},
#         },
#     }
#
#     # Получаем конфигурацию для текущего URL
#     config_data = URL_CONFIG.get(params.get("url"))
#
#     if config_data:
#         # Если есть префикс, проверяем существование файла
#         if config_data["prefix"]:
#             my_file = await get_path_to_json(
#                 prefix=config_data["prefix"], data=params.get("itemId")
#             )
#             if my_file.is_file():
#                 print(f"File {my_file} already exists for {params.get('url')}")
#                 return
#
#         # Сохраняем данные
#         await save_data_json(
#             data=result,
#             folder=config_data["folder"],
#             config_data=config_data["args"],
#         )
#         print(f"Saved in /{config_data['folder']}")
#
#
# async def save_data_json(
#         data,
#         config_data,
#         folder: str = None,
# ):
#     page = config_data.get("page")
#     query = config_data.get("query")
#     item_id = config_data.get("itemId")
#
#     try:
#         folder_path = os.path.join(config.BASE_DIR, FAKE_MAIN_FOLDER, folder)
#         if not os.path.exists(folder_path):
#             os.makedirs(folder_path)
#
#         if item_id and folder == DETAIL_FAKE_FOLDER:
#             file_name = "detail_{0}.json".format(item_id)
#
#         elif item_id and folder == REVIEW_FAKE_FOLDER:
#             file_name = "review_{0}.json".format(item_id)
#
#         else:
#             file_name = "{0}_{1}.json".format(query.replace(" ", "_").lower(), page)
#
#         file_path = os.path.join(folder_path, file_name)
#         with open(file_path, "w") as file:
#             json.dump(data, file, ensure_ascii=False, indent=4)
#
#     except AttributeError:
#         file_name = "{0}.json".format(item_id)
#         file_path = os.path.join(
#             config.BASE_DIR, FAKE_MAIN_FOLDER, "_favorite", file_name
#         )
#         with open(file_path, "w") as file:
#             json.dump(data, file, ensure_ascii=False, indent=4)
#
#
# async def get_path_to_json(prefix, data: str | tuple):
#     if isinstance(data, tuple):
#         file_name = "{0}_{1}.json".format(data[0].replace(" ", "_").lower(), data[1])
#     else:
#         file_name = "{0}_{1}.json".format(prefix, data)
#     return Path(
#         os.path.join(
#             config.BASE_DIR, FAKE_MAIN_FOLDER, PREFIX_FOLDER[prefix], file_name
#         )
#     )
#
#
# async def request_api_fake(params):
#     if params.get("itemId"):
#         prefix = "detail"
#         path = await get_path_to_json(prefix, params.get("itemId"))
#     elif params.get("filters"):
#         prefix = "review"
#         path = await get_path_to_json(prefix, params.get("itemId"))
#     else:
#         prefix = "list"
#         path = await get_path_to_json(prefix, (params.get("q"), params.get("page")))
#     try:
#         with open(path, "r") as file:
#             data = json.load(file)
#     except FileNotFoundError:
#         path = await get_path_to_json("error", (prefix, 1))
#         with open(path, "r") as file:
#             data = json.load(file)
#     finally:
#         return data


# async def request_api(params) -> dict:
#     for key, value in params.items():
#         if value:
#             conf.querystring[key] = value
#     msg = "▶️▶️▶️ REQUEST API {0}".format(params)
#     log.info_log.info(msg)
#     if config.FAKE_MODE:
#         result = await request_api_fake(params)
#     else:
#         try:
#             timeout = httpx.Timeout(10.0, read=None)
#             async with httpx.AsyncClient() as client:
#                 response = await client.get(
#                     url="/".join([conf.base_url, params.get("url")]),
#                     headers=conf.headers,
#                     params=conf.querystring,
#                     timeout=timeout,
#                 )
#         except httpx.HTTPError as error:
#             msg = "⚠️ HTTP ERROR\n{0}".format(error)
#             log.error_log.exception(msg)
#             raise exceptions.FreeAPIExceededError(msg)
#         result = response.json()
#         if "message" in result:
#             msg = "⚠️ request error\n{0}".format(result.get("message"))
#             log.error_log.error(msg)
#             raise exceptions.FreeAPIExceededError(message=msg)
#         await save_fake_data(result, params)
#
#     return result

#####################################################################################
