import os
from typing import Optional, Union

from aiogram.filters import Filter
from aiogram.types import FSInputFile, Message,CallbackQuery
from aiogram.utils.formatting import HashTag, as_list, as_marked_section
from httpx import Response

from config import conf
from pagination import Paginator


class CustomFilter(Filter):
    def __init__(self, command: Union[str, list]):
        self.command = command

    async def __call__(self, message: Message | CallbackQuery) -> bool:
        if isinstance(message, CallbackQuery):
            print('CallbackQuery ', message.data)
            return message.data.startswith(self.command)
        print('Message ', message.text)
        return message.text.startswith("/{0}".format(self.command))


def get_price_range(_list) -> Optional[str]:
    if _list is not None:
        sorted_prices = sorted(set(_list), reverse=True)
        return "{} - {}".format(sorted_prices[0], sorted_prices[-1])
    return None


def card_info(item, currency):
    image = ":".join(["https", item["item"]["image"]])
    msg = "{0:.50}\n".format(item["item"]["title"])
    msg = msg + "🔥 продано: <b>{0}</b>\n".format(item["item"]["sales"])
    msg = msg + "💵 цена: <b>{0}</b>".format(
        item["item"]["sku"]["def"]["promotionPrice"])
    msg = msg + "{0}\n".format(currency)
    msg = msg + "{0}".format(":".join(["https", item["item"]["itemUrl"]]))
    return msg, image


def detail_info(i):
    properties = i["result"]["item"]["properties"]["list"]
    msg = "характеристики:"
    for prop in properties:
        msg = msg + "- {0}: {1}\n".format(prop["name"], prop["value"])
    return msg


async def get_detail_info(i):
    try:
        print('\ndetail_info_2=', i["result"]["item"]["title"])
    except Exception as err:
        print(i)
        print("❌ERROR: ", err)
    msg = ""
    title = i["result"]["item"]["title"]
    item_url = ":".join(["https", i["result"]["item"]["itemUrl"]])
    properties_list = i["result"]["item"]["properties"]["list"]
    promotion_price = i["result"]["item"]["sku"]["base"][0]["promotionPrice"]
    size = i["result"]["item"]["sku"]["props"][0]["values"]
    reviews = i["result"]["reviews"]["count"]
    average_star = i["result"]["reviews"]["averageStar"]
    shipping_out_days = i["result"]["delivery"]["shippingOutDays"]
    weight = i["result"]["delivery"]["packageDetail"]["weight"]
    length = i["result"]["delivery"]["packageDetail"]["height"]
    width = i["result"]["delivery"]["packageDetail"]["width"]
    height = i["result"]["delivery"]["packageDetail"]["height"]
    store_title = i["result"]["seller"]["storeTitle"]
    store_url = ":".join(["https", i["result"]["seller"]["storeUrl"]])

    msg = msg + "{0}\n\n{1:.100}\n".format(item_url, title)
    msg = msg + "\n\t💰 Цена:\n\t".upper()
    msg = msg + "\t{0}\n".format(promotion_price)
    try:
        msg = msg + "\n\tРазмеры:\n\t".upper()
        for s in size:
            msg = msg + "\t- {0}\n".format(s["name"])
    except Exception as err:
        print("❌ERROR: ", err)
    try:
        msg = msg + "\n\t характеристики:\n".upper()
        for prop in properties_list:
            msg = msg + "\t- {0}: {1}\n".format(prop["name"], prop["value"])
    except Exception as err:
        print("❌ERROR: ", err)

    try:
        msg = msg + "\n📈 Продажи: {0}\n🔝 Рейтинг: {1}\n".format(
            reviews,
            average_star,
        )
    except Exception as err:
        print("❌ERROR: ", err)
    try:
        msg = msg + "\n🚚 Доставка: ".upper()
        msg = msg + "{0} дн.\n\t- вес:  {1} кг\n".format(
            shipping_out_days, weight
        )
        msg = (
                msg
                + "\t- длина: {0} см\n\t- ширина: {1} см\n\t- высота: {2}см \n".format(
            length, width, height
        )
        )
        msg = msg + "\n🏪 Продавец:\n".upper()
        msg = msg + "\t{0}\n\t{1}\n".format(store_title, store_url)
    except Exception as err:
        print("❌ERROR: ", err)
    return msg


def get_color_img(i):
    images = []
    print('\ndetail_color_img = ', i["result"]["item"]["sku"]["props"])
    try:
        image_list = i["result"]["item"]["sku"]["props"][1]["values"]
        for i in image_list:
            img = ":".join(["https", i["image"]])
            images.append(img)
        return images
    except (IndexError, KeyError):
        return None


def detail_img(i):
    images = []
    try:
        image_list = i["result"]["item"]["description"]["images"][:5]
        for img in image_list:
            img = ":".join(["https", img])
            images.append(img)
        return images
    except (IndexError, KeyError):
        return None


async def history_info(i):
    msg = ''
    msg = msg + "⚙️ команда:\t<b>{0}</b>\n".format(i.command)
    msg = msg + "📅 дата:\t{0}\t".format(i.date.strftime('%d %b %Y'))
    msg = msg + "🕐 время:\t{0}\n".format(i.date.strftime('%H:%M:%S'))
    if i.search_name:
        msg = msg + "🔎 поиск:\t{0}\n".format(i.search_name)
    if i.result_qnt:
        msg = msg + "🔟 количество:\t{0}\n".format(i.result_qnt)
    if i.price_range:
        msg = msg + "⚪️ диапазон цен:\t{0}\n".format(i.price_range)
    if i.title:
        msg = msg + "✅ :\t{0:.100}\n".format(i.title)
    if i.price:
        msg = msg + "🟠 :\t{0} RUB\n".format(i.price)
    if i.reviews:
        msg = msg + "👀 просмотры:\t{0}\n".format(i.reviews)
    if i.stars:
        msg = msg + "⭐️ рейтинг:\t{0}\n".format(i.stars)
    if i.url:
        msg = msg + "{0}\n".format(i.url.split("//")[1])
    return msg


def unpacking_subcategory(sub_cat_list: list, query: str = None):
    msg = ''
    for category in sub_cat_list:
        subcategory_name = category["name"]
        if subcategory_name:
            if query in subcategory_name.lower():
                msg = msg + "{0}\n".format(category["name"])
    return msg


def category_info(items: dict, query: str = None):
    count = 0
    query = query.lower()
    # print(f"### {query=  }")
    category_name = items.get("name")
    category_id = items.get("id")
    sub_category_name = items.get("list")
    msg = ''
    cat_name = category_name.lower()

    if query in cat_name:
        count += 1
        msg = unpacking_subcategory(
            query=query,
            sub_cat_list=sub_category_name
        )
        # print(f"🔥 {query} in ", cat_name)
        # print(cat_name)
        # print(msg)
        # msg = msg + "\n#{0}\n".format(query)
    else:
        for sub_cat in sub_category_name:
            count += 1
            sub_cat_name = sub_cat.get("name")
            if sub_cat_name:
                sub_cat_name = sub_cat_name.lower()

                if query.lower() in sub_cat_name:
                    msg = unpacking_subcategory(
                        query=query,
                        sub_cat_list=sub_category_name
                    )
                    # print(f"✅ {query} in ", sub_cat_name)
                    # print(cat_name)
                    # print(msg)
                    # msg = msg + "\n#{0}\n".format(query)
                    break
    return msg, category_name, str(category_id), count


def separate_img_by_ten(images: list, num: int = 9):
    for i in range(0, len(images), num):
        yield list(images[i: i + num])


def pages(paginator: Paginator):
    buttons = dict()
    if paginator.has_previous():
        buttons["◀ пред."] = "previous"
    if paginator.has_next():
        buttons["след. ▶"] = "next"
    return buttons


async def deserialize_item_detail(response: dict, user_id: int) -> dict:
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
        image_full_path = ":".join(["https", item["images"][0]])
    except:
        image_full_path = FSInputFile(
            os.path.join(conf.static_path, 'category.png'))
    data["image"] = image_full_path

    return data
