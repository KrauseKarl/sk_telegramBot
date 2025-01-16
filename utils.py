import re

import requests
from aiogram.utils.formatting import as_list, as_marked_section, HashTag, Bold

from config import settings


async def request_handler(current_url, q=None, sort=None) -> dict:
    headers = {
        "x-rapidapi-key": settings.api_key.get_secret_value(),
        "x-rapidapi-host": settings.host,
    }
    base_url = settings.url
    url = base_url + "/" + current_url
    querystring = {
        "locale": "ru_RU",
        "currency": "RUB",
        "region": "RU",
    }
    if q and sort:
        querystring["q"] = q
        querystring["sort"] = sort
    response = requests.get(url=url, headers=headers, params=querystring)
    return response.json()


async def request_detail(item_id: str):
    url = "https://aliexpress-datahub.p.rapidapi.com/item_desc_2"
    querystring = {
        "itemId": item_id,
        "locale": "ru_RU",
        "currency": "RUB",
        "region": "RU",
    }
    headers = {
        "x-rapidapi-key": settings.api_key.get_secret_value(),
        "x-rapidapi-host": settings.host,
    }
    response = requests.get(url, headers=headers, params=querystring)
    return response.json()


async def request_detail_2(item_id: str):
    url = "https://aliexpress-datahub.p.rapidapi.com/item_detail_6"
    querystring = {
        "itemId": item_id,
        "locale": "ru_RU",
        "currency": "RUB",
        "region": "RU",
    }
    headers = {
        "x-rapidapi-key": settings.api_key.get_secret_value(),
        "x-rapidapi-host": settings.host,
    }
    response = requests.get(url, headers=headers, params=querystring)

    return response.json()


def card_info(i, currency):
    title = i["item"]["title"]
    sales = i["item"]["sales"]
    price = i["item"]["sku"]["def"]["promotionPrice"]
    image_url = ":".join(["https", i["item"]["itemUrl"]])
    image = ":".join(["https", i["item"]["image"]])
    msg = "{0}\n название: {1}\n продано: {2}\n цена: {3} {4}\n{5}".format(
        image_url, title, sales, price, currency, image
    )
    return msg


def detail_info(i):
    properties = i["result"]["item"]["properties"]['list']
    msg = "характеристики:"
    for prop in properties:
        msg = msg + "- {0}: {1}\n".format(
            prop["name"], prop["value"]
        )
    return msg


def detail_info_2(i):
    try:
        print(i["result"]["item"]["title"])
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

    msg = msg + "{0}\n\n{1}\n".format(item_url, title)
    msg = msg + "\n\t💰 Цена:\n\t".upper()
    msg = msg + "\t{0}\n".format(promotion_price)
    try:
        msg = msg + "\n\tРазмеры:\n\t".upper()
        for s in size:
            msg = msg + "\t- {0}\n".format(
                s["name"]
            )
    except Exception as err:
        print("❌ERROR: ", err)
    try:
        msg = msg + "\n\t характеристики:\n".upper()
        for prop in properties_list:
            msg = msg + "\t- {0}: {1}\n".format(
                prop["name"], prop["value"]
            )
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
            shipping_out_days,
            weight
        )
        msg = msg + "\t- длина: {0} см\n\t- ширина: {1} см\n\t- высота: {2}см \n".format(
            length,
            width,
            height
        )
        msg = msg + "\n🏪 Продавец:\n".upper()
        msg = msg + "\t{0}\n\t{1}\n".format(
            store_title,
            store_url
        )
    except Exception as err:
        print("❌ERROR: ", err)
    return msg


def detail_color_img(i):
    images = []
    image_list = i["result"]["item"]["sku"]["props"][1]["values"]
    for i in image_list:
        print(i)
        img = ":".join(["https", i['image']])
        images.append(img)
    return images


def detail_img(i):
    images = []
    image_list = i["result"]["item"]["description"]["images"]
    for img in image_list:
        img = ":".join(["https", img])
        images.append(img)
    return images


def category_info(i: dict, q: str = None):
    category_name = i["name"]
    print('=' * 100)
    print('', category_name)
    msg = None
    item_list = []
    for name in category_name.split(' '):
        # print('-', i["list"])
        if name.startswith(q):
            # print('', category_name)
            msg = "{0}\n".format(category_name)
            sub_category_name = i["list"]
            # print('', sub_category_name)
            for s in sub_category_name:
                # print('-', sub_category_name)
                print('\t\t\t', s["name"], s['id'])
                sub_name = s["name"]
                sub_id = s['id']
                # print('---', sub_name)
                result = f"{sub_name} [{sub_id}]({category_name})"
                item_list.append(result)
                msg = msg + "- {0}\n".format(sub_name)
        # await message.answer(msg)

    # sub_category_name = i["list"]
    # if sub_category_name is not None:
    #     for s in sub_category_name:
    #         sub_name = s["name"]
    #         if sub_name is not None:
    #             sub_name_list = re.split('//| ', sub_name)
    #             # sub_name_list = sub_name.split('/').split(' ')
    #             print(f'\t{sub_name_list}')
    #             for sub_name in sub_name_list:
    #                 if sub_name.startswith(q):
    #                     msg = "{0}\n".format(category_name)
    #                     msg = msg + "- {0}\n".format(sub_name)
    hashtag = "#{}".format(q)

    if len(item_list) > 0:
        content = as_list(
            as_marked_section(
                # Bold(f"По запросу - {q}:"),
                *item_list,
                # marker="✅ ",
            ),
            HashTag(hashtag),
            sep="\n\n",
        )
    else:
        content = None
    print('=' * 100)
    return content
