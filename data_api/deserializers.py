import json
import uuid
from datetime import timedelta
from typing import Optional

from redis import asyncio as aioredis
from aiogram.filters.callback_data import CallbackData
from redis import AuthenticationError
# from redis.asyncio.client import Redis, StrictRedis
# from redis.client import Redis, StrictRedis

from database.exceptions import FreeAPIExceededError
from database.orm import *
from utils.media import *
from utils.message_info import card_info, get_price_range


async def redis_flush_keys() -> aioredis.Redis:
    try:
        client = await aioredis.Redis()
        ping = await client.ping()
        keys = await client.keys()
        print(f"🟡{sorted(keys)}")
        if ping is True:
            await client.flushall()
            print("🚫 Redis keys deleted")
            keys = await client.keys()
            print(f"🟡{sorted(keys)}")
            return client
    except AuthenticationError:
        print("AuthenticationError")


async def redis_connect() -> aioredis.Redis:
    try:
        client = await aioredis.Redis()
        ping = await client.ping()

        if ping is True:
            return client
    except AuthenticationError:
        print("AuthenticationError")


async def get_routes_from_cache(key: str):
    """Get data from redis."""
    try:
        client = await redis_connect()
        val = await client.get(key)
        return json.loads(val)
    except TypeError:
        return None


async def set_routes_to_cache(key: str, value: str) -> bool:
    """Set data to redis."""
    client = await redis_connect()
    state = await client.setex(
        key,
        timedelta(seconds=60 * 60),
        value=value,
    )
    try:
        keys = await client.keys()
        for k in sorted(keys):
            print(f"🟧 {k}")
    except:
        pass
    return state


async def deserialize_item_detail(
        response: dict, user_id: int
) -> Optional[dict]:
    """

    :param response:
    :param user_id:
    :return:
    """
    data = dict()

    item = response["result"]["item"]
    reviews = response["result"]["reviews"]

    data["user"] = user_id
    data["command"] = "item detail"
    data["title"] = item.get("title")
    data["price"] = item.get("sku").get("base")[0].get("promotionPrice")
    data["reviews"] = reviews.get("count")
    data["star"] = reviews.get("averageStar")
    data["url"] = ":".join(["https", item.get("itemUrl")])
    # try:
    #     image_url = ":".join(["https", item["images"][0]])
    #     path, file_name = await make_default_size_image(image_url)
    # except KeyError:
    #     file_name = None
    # data["image"] = file_name

    try:
        image_url = ":".join(["https", item["images"][0]])
    except KeyError:
        image_url = None

    data["image"] = image_url

    return data


class FavoriteCBF(CallbackData, prefix="fav"):
    product_id: str
    title: str
    price: str
    reviews: str
    stars: str
    url: str

    # image: str


async def deserialize_item_list(
        response: dict,
        user_id: int,
        data: dict,
        cache_key: str = None
):
    """

    :param response:
    :param user_id:
    :param data:
    :return:
    """
    price_range_list = []
    result_list = []
    # ranges = int(data["qnt"])
    # item_list = response["result"]["resultList"][:ranges]
    item_list = response["result"]["resultList"]
    currency = response["result"]["settings"]["currency"]

    # todo save api response to redis

    # make UUID-key
    print(f"\n🟥🟥🟥🟥 {cache_key= } 🟥🟥🟥\n")

    # check cache
    cache_data = await get_routes_from_cache(cache_key)

    # get_or_create cache
    if cache_data is None:
        value = json.dumps(item_list, ensure_ascii=False, indent=4)
        await set_routes_to_cache(key=cache_key, value=value)
    # save in file .json
    cache_file_path = os.path.join(config.CACHE_PATH, f'{cache_key}.json')
    with open(cache_file_path, 'w', encoding='utf-8') as file:
        json.dump(item_list, file, ensure_ascii=False, indent=4)

    # todo save api response to redis

    for item in item_list:
        msg, img = card_info(item, currency)
        price = item["item"]["sku"]["def"]["promotionPrice"]
        item_id = item["item"]["itemId"]
        kb = await builder_kb(
            data=[
                {"👀 подробно": "{0}_{1}".format("item", item_id)},
                {"⭐️ в избранное": "{0}_{1}".format("fav_pre_add", item_id)}
            ],
            size=(2,)
        )
        price_range_list.append(price)
        result_list.append((msg, img, kb))

    await orm_make_record_request(
        HistoryModel(
            user=user_id,
            command='search',
            price_range=get_price_range(price_range_list),
            # result_qnt=int(ranges),
            result_qnt=int(len(item_list)),
            search_name=data['product'],
        ).model_dump())

    return result_list, get_price_range(price_range_list)


async def deserialize_item_cache(item_list):
    result_list = []
    currency = "RUB"

    for item in item_list:
        msg, img = card_info(item, currency)
        item_id = item["item"]["itemId"]
        kb = await builder_kb(
            data=[
                {
                    "⭐️ в избранное": "{0}_{1}".format(
                        "fav_pre_add", item_id
                    )
                }
            ],
            size=(2,)
        )
        result_list.append((msg, img, kb))

    return result_list
