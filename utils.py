import io
import os.path
import urllib
from typing import List, Optional
from urllib.parse import urlparse, unquote
from urllib.request import urlretrieve
from PIL import Image

from aiogram.types import FSInputFile, InlineKeyboardButton, InputMediaPhoto
from aiogram.utils.keyboard import InlineKeyboardBuilder

from core import *
from core import config
from database.models import *
from database.orm import *
from keyboards import *
from pagination import *


async def get_error_answer_photo(error: Exception) -> tuple[str, FSInputFile]:
    photo = await get_fs_input_hero_image("error")
    msg = "⚠️ Произошла ошибка {0}".format(error)
    return msg, photo


async def get_error_answer_media(error: Exception) -> InputMediaPhoto:
    return await get_input_media_hero_image(
        "error",
        "⚠️ Произошла ошибка {0}".format(error)
    )


async def make_paginate_history_list(
        history_list: List[History], page: int = 1
):
    if len(history_list) == 0:
        return 'у вас нет истории просмотров', menu_kb
    kb = InlineKeyboardBuilder()
    call_back_data = "page_next_{0}".format(int(page) + 1)
    kb.add(InlineKeyboardButton(text='След. ▶', callback_data=call_back_data))
    kb.add(InlineKeyboardButton(text='меню', callback_data="menu"))
    paginator = Paginator(history_list, page=page)
    history_items = paginator.get_page()[0]
    msg = await history_info(history_items)
    msg = msg + "\n{0} из {1}".format(page, paginator.pages)
    keyboard = kb.adjust(1, 1).as_markup()
    return msg, keyboard


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
    msg = msg + "\n{0}".format(":".join(["https", item["item"]["itemUrl"]]))
    return msg, image


def detail_info(i):
    properties = i["result"]["item"]["properties"]["list"]
    msg = "характеристики:"
    for prop in properties:
        msg = msg + "- {0}: {1}\n".format(prop["name"], prop["value"])
    return msg


async def get_detail_info(i):
    # try:
    #     print('\ndetail_info_2=', i["result"]["item"]["title"])
    # except Exception as err:
    #     print(i)
    #     print("❌ERROR: ", err)
    msg = ""
    title = i["result"]["item"]["title"]
    item_url = ":".join(["https", i["result"]["item"]["itemUrl"]])
    properties_list = i["result"]["item"]["properties"]["list"]
    promotion_price = i["result"]["item"]["sku"]["base"][0]["promotionPrice"]


    try:
        prop = i["result"]["item"]["sku"]["props"]
        if prop[0].get("name") in ["Size", "Размер"] and prop[0].get("name") not in ["Color", "Цвет"]:
            size = prop[0]["values"]
        else:
            size = prop[1]["values"]
    except IndexError:
        size = None

    reviews = i["result"]["reviews"]["count"]
    average_star = i["result"]["reviews"]["averageStar"]
    shipping_out_days = i["result"]["delivery"]["shippingOutDays"]
    weight = i["result"]["delivery"]["packageDetail"]["weight"]
    length = i["result"]["delivery"]["packageDetail"]["height"]
    width = i["result"]["delivery"]["packageDetail"]["width"]
    height = i["result"]["delivery"]["packageDetail"]["height"]
    store_title = i["result"]["seller"]["storeTitle"]
    store_url = ":".join(["https", i["result"]["seller"]["storeUrl"]])

    msg = msg + "{0}\n\n{1:.50}\n".format(item_url, title)
    msg = msg + "💰 {0}\n".format(promotion_price)
    try:
        msg = msg + "<u>Размеры:</u> ".upper()
        for s in size:
            msg = msg + "\t {0} ".format(s["name"])
    except Exception as err:
        print("❌ERROR: ", err)
    try:
        msg = msg + "\n<u>характеристики:</u>\n".upper()
        for prop in properties_list:
            msg = msg + "\t- {0}: {1}\n".format(prop["name"], prop["value"])
    except Exception as err:
        print("❌ERROR: ", err)

    try:
        msg = msg + "\n📈 Продажи: {0}\t⭐️ Рейтинг: {1}\n".format(
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
    return msg[:(MESSAGE_LIMIT - 1)] if len(msg) > MESSAGE_LIMIT else msg


def get_color_img(i):
        images = []
    # print('\ndetail_color_img = ', i["result"]["item"]["sku"]["props"])
    # try:
        prop = i["result"]["item"]["sku"]["props"]
        print(f"\n\nPROP\n {prop }\n\n")
        print(prop[0].get("name"))
        print(prop[1].get("name"))
        if prop[0].get("name") in ['Цвет', 'Color']:
            image_list = prop[0]["values"]
        else:
            image_list = prop[1]["values"]
        print(image_list)
        for i in image_list:
            img = ":".join(["https", i["image"]])
            images.append(img)
        return images
    # except (IndexError, KeyError):
    #     return None


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
    msg = msg + "📅 {0}\n".format(i.date.strftime('%d %b %Y'))
    msg = msg + "🕐 {0}\n".format(i.date.strftime('%H:%M:%S'))
    if i.search_name:
        msg = msg + "🔎 поиск:\t{0:.5}\n".format(i.search_name)
    if i.result_qnt:
        msg = msg + "🔟 количество:\t{0}\n".format(i.result_qnt)
    if i.price_range:
        msg = msg + "⚪️ диапазон цен:\t{0}\n".format(i.price_range)
    if i.title:
        msg = msg + "✅ {:.30}\n".format(i.title)
    if i.price:
        msg = msg + "🟠 {0} RUB\n".format(i.price)
    if i.reviews:
        msg = msg + "👀 {0}\n".format(i.reviews)
    if i.stars:
        msg = msg + "⭐️{0}\n".format(i.stars)
    if i.url:
        msg = msg + "{0}\n".format(i.url.split("//")[1])
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
        print(f"🔥 {query} in ", cat_name)
        print(cat_name)
        print(msg)
        msg = msg + "\n#{0}\n".format(query)
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
                    print(f"✅ {query} in ", sub_cat_name)
                    print(cat_name)
                    print(msg)
                    msg = msg + "\n#{0}\n".format(query)
                    break
    return msg, category_name, str(category_id), count


def unpacking_subcategory(sub_cat_list: list, query: str = None):
    msg = ''
    for category in sub_cat_list:
        subcategory_name = category["name"]
        if subcategory_name:
            if query in subcategory_name.lower():
                msg = msg + "{0}\n".format(category["name"])
    return msg


def separate_img_by_ten(images: list, num: int = 9):
    for i in range(0, len(images), num):
        yield list(images[i: i + num])


async def deserialize_item_detail(response: dict, user_id: int) -> Optional[dict]:
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


async def deserialize_item_list(response: dict, user_id: int, data: dict) -> List[tuple]:
    price_range_list = []
    data_result_list = []
    ranges = int(data["qnt"])
    item_list = response.get("result").get("resultList")[:ranges]
    currency = response.get("result").get("settings")["currency"]

    for item in item_list:
        msg, img = card_info(item, currency)
        price = item["item"]["sku"]["def"]["promotionPrice"]
        kb = await item_kb_2(
            "item",
            item["item"]["itemId"],
            text='подробно'
        )
        price_range_list.append(price)
        data_result_list.append((msg, img, kb))

    await orm_make_record_request(
        HistoryModel(
            user=user_id,
            command='search',
            price_range=get_price_range(price_range_list),
            result_qnt=int(ranges),
            search_name=data['product'],
        ).model_dump())
    return data_result_list


async def get_fs_input_hero_image(value: str) -> FSInputFile:
    return FSInputFile(os.path.join(conf.static_path, HERO[value]))


async def get_input_media_hero_image(value: str, msg: str = None) -> InputMediaPhoto:
    return InputMediaPhoto(
        media=await get_fs_input_hero_image(value),
        caption=msg
    )


async def parse_url(url: str) -> str:
    """Парсит имя файла из url."""
    return unquote(Path(urlparse(url).path).name)


async def make_default_size_image(url: str) -> tuple[Optional[str], Optional[str]]:
    """
    Изменяет размер (1024х576) изображения товара и
    сохраняет в директории `static/products`
    """
    try:
        file_name = await parse_url(url)
        full_path = os.path.join(config.IMAGE_PATH, file_name)

        fd = urllib.request.urlopen(url)
        input_img_file = io.BytesIO(fd.read())

        img = Image.open(input_img_file)
        img.thumbnail((config.THUMBNAIL, config.HEIGHT))
        img.save(fp=full_path, format=config.IMG_FORMAT)
        input_width, input_height = img.size

        bg = Image.new('RGB', (config.WIDTH, config.HEIGHT))
        bg_width, bg_height = bg.size
        offset = ((bg_width - input_width) // 2, (bg_height - input_height) // 2)
        bg.paste(im=img, box=offset)
        bg.save(fp=full_path, format=config.IMG_FORMAT)
        bg.close()
        img.close()

        return full_path, file_name
    except Exception:
        return None, None
