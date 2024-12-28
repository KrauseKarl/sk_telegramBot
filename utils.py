import requests

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
    msg = "название: {0}\n продано: {1}\n цена: {2} {3}\n{5}".format(
        title, sales, price, currency, image_url, image
    )
    # await message.answer(msg)
    return msg


def category_info(i):
    category_name = i["name"]
    msg = "{0}\n".format(category_name)
    sub_category_name = i["list"]
    for s in sub_category_name:
        sub_name = s["name"]
        msg = msg + "- {0}\n".format(sub_name)
    # await message.answer(msg)
    return msg
