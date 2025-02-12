from typing import Optional

from aiogram.filters.callback_data import CallbackData

from database.orm import *
from utils.media import *
from utils.message_info import card_info, get_price_range


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
    try:
        image_url = ":".join(["https", item["images"][0]])
        path, file_name = await make_default_size_image(image_url)
    except KeyError:
        file_name = None
    data["image"] = file_name
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
        response: dict, user_id: int, data: dict
) -> tuple[tuple, str]:
    """

    :param response:
    :param user_id:
    :param data:
    :return:
    """
    price_range_list = []
    result_list = []
    ranges = int(data["qnt"])
    item_list = response["result"]["resultList"][:ranges]
    currency = response["result"]["settings"]["currency"]

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
            result_qnt=int(ranges),
            search_name=data['product'],
        ).model_dump())

    return result_list, get_price_range(price_range_list)
