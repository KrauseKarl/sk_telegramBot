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


def card_info(i, currency):
    title = i["item"]["title"]
    sales = i["item"]["sales"]
    price = i["item"]["sku"]["def"]["promotionPrice"]
    image_url = ":".join(["https", i["item"]["itemUrl"]])
    image = ":".join(["https", i["item"]["image"]])
    msg = "название: {0}\n продано: {1}\n цена: {2} {3}\n{4}\n{5}".format(
        title, sales, price, currency, image_url, image
    )
    # await message.answer(msg)
    return msg


def category_info(i: dict, q: str = None):
    category_name = i["name"]
    print('', category_name)
    msg = None
    item_list = []
    for name in category_name.split(' '):
        if name.startswith(q):
            print('', category_name)
            msg = "{0}\n".format(category_name)
            sub_category_name = i["list"]
            print('', sub_category_name)
            for s in sub_category_name:
                # print('-', sub_category_name)
                sub_name = s["name"]
                # print('---', sub_name)
                result = f"{sub_name} ({category_name})"
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
                Bold(f"По запросу - {q}:"),
                *item_list,
                marker="✅ ",
            ),
            HashTag(hashtag),
            sep="\n\n",
        )
    else:
        content = None

    return content
