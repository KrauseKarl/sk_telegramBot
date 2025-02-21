from typing import Optional

from database.pagination import *


def get_price_range(_list) -> Optional[str]:
    """

    :param _list:
    :return:
    """
    if _list is not None:
        sorted_prices = sorted(set(_list), reverse=True)
        return "{} - {}".format(sorted_prices[0], sorted_prices[-1])
    return None


# INFO FOR TELEGRAM ANSWER MESSAGE #########################################################
def card_info(item, currency) -> tuple[str, str]:
    """

    :param item:
    :param currency:
    :return:
    """
    image = ":".join(["https", item["item"]["image"]])
    msg = "{0:.50}\n".format(item["item"]["title"])
    msg = msg + "🔥 продано: <b>{0}</b>\n".format(item["item"]["sales"])
    msg = msg + "💵 цена: <b>{0}</b>".format(
        item["item"]["sku"]["def"]["promotionPrice"])
    msg = msg + "{0}\n".format(currency)
    msg = msg + "\n{0}".format(":".join(["https", item["item"]["itemUrl"]]))
    return msg, image


def detail_info(i) -> str:
    """

    :param i:
    :return:
    """
    properties = i["result"]["item"]["properties"]["list"]
    msg = "характеристики:"
    for prop in properties:
        msg = msg + "- {0}: {1}\n".format(prop["name"], prop["value"])
    return msg


async def get_detail_info(i) -> str:
    """

    :param i:
    :return:
    """
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
        if (prop[0].get("name") in ["Size", "Размер"] and
                prop[0].get("name") not in ["Color", "Цвет"]):
            size = prop[0]["values"]
        else:
            size = prop[1]["values"]
    except IndexError:
        size = None

    reviews = i["result"]["reviews"]["count"]
    average_star = i["result"]["reviews"]["averageStar"]
    delivery = i["result"]["delivery"]
    shipping_out_days = delivery["shippingOutDays"]
    weight = delivery["packageDetail"]["weight"]
    length = delivery["packageDetail"]["height"]
    width = delivery["packageDetail"]["width"]
    height = delivery["packageDetail"]["height"]
    store_title = i["result"]["seller"]["storeTitle"]
    store_url = ":".join(["https", i["result"]["seller"]["storeUrl"]])

    msg = msg + "{0}\n\n{1:.50}\n".format(item_url, title)
    msg = msg + "💰 {0}\n".format(promotion_price)
    try:
        msg = msg + "<u>Размеры:</u> ".upper()
        for s in size:
            msg = msg + "\t {0} ".format(s["name"])
    except Exception as err:
        print("❌ERROR:[Размеры]", err)
    try:
        msg = msg + "\n<u>характеристики:</u>\n".upper()
        for prop in properties_list:
            msg = msg + "\t- {0}: {1}\n".format(prop["name"], prop["value"])
    except Exception as err:
        print("❌ERROR:[характеристики] ", err)

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
            length,
            width,
            height
        )
        )
        msg = msg + "\n🏪 Продавец:\n".upper()
        msg = msg + "\t{0}\n\t{1}\n".format(store_title, store_url)
    except Exception as err:
        print("❌ERROR: ", err)
    return msg[:(MESSAGE_LIMIT - 1)] if len(msg) > MESSAGE_LIMIT else msg


def get_color_img(item: dict) -> Optional[List[str]]:
    """

    :param item:
    :return:
    """
    images = []
    try:
        prop = item["result"]["item"]["sku"]["props"]
        if ('Color' in prop[0].get("name") or
                'Цвет' in prop[0].get("name")):
            image_list = prop[0]["values"]
        else:
            image_list = prop[1]["values"]
        for i in image_list:
            img = ":".join(["https", i["image"]])
            images.append(img)
        return images
    except (IndexError, KeyError):
        return None


def detail_img(item) -> Optional[List[str]]:
    """

    :param item:
    :return:
    """
    images = []
    try:
        image_list = item["result"]["item"]["description"]["images"][:5]
        for img in image_list:
            img = ":".join(["https", img])
            images.append(img)
        return images
    except (IndexError, KeyError):
        return None


async def history_info(item) -> str:
    """

    :param item:
    :return:
    """
    msg = "⚙️ команда:\t<b>{0}</b>\n\n".format(item.command)
    msg += "📅 {0}\t".format(item.date.strftime('%d %b %Y'))
    msg += "🕐 {0}\n".format(item.date.strftime('%H:%M:%S'))
    if item.search_name:
        msg = msg + "🔎 поиск:\t{0:.20}\n".format(item.search_name)
    if item.price_min and item.price_max:
        msg = msg + "⚪️ диапазон цен:\t{0}-{1}\n".format(item.price_min,  item.price_max)
    if item.title:
        msg = msg + "✅ {:.30}\n".format(item.title)
    if item.price:
        msg = msg + "🟠 {0} RUB\n".format(item.price)
    if item.reviews:
        msg = msg + "👀 промоторы {0}\n".format(item.reviews)
    if item.stars:
        msg = msg + "⭐️рейтинг {0}\n".format(item.stars)
    if item.url:
        msg = msg + "{0}\n".format(item.url.split("//")[1])
    if item.sort:
        msg = msg + "📊 отсортировано: {0}\n".format(item.sort)

    return msg


async def favorite_info(item) -> str:
    """

    :param item:
    :return:
    """
    msg = "📅\t{0}\n".format(item.date.strftime('%d %b %Y'))
    msg = msg + "🕐\t{0}\n".format(item.date.strftime('%H:%M:%S'))
    msg = msg + "🆔\t<u>id</u>:\t{0}\n".format(item.product_id)
    msg = msg + "✅\t{:.100}\n".format(item.title)
    msg = msg + "🟠\t<i>цена</i>:\t{0}\tRUB\n".format(item.price)
    msg = msg + "👀\t<i>просмотров</i>:\t{0}\n".format(item.reviews)
    msg = msg + "⭐️\t<i>рейтинг</i>:\t{0}\n".format(item.stars)
    msg = msg + "{0}\n".format(item.url.split("//")[1])
    return msg


def category_info(items: dict, query: str = None):
    """

    :param items:
    :param query:
    :return:
    """
    count = 0
    query = query.lower()
    category_name = items.get("name")
    category_id = items.get("id")
    sub_category_list = items.get("list")
    msg = ''
    cat_name = category_name.lower()
    result = []
    if query in cat_name:
        count += 1
        msg = unpacking_subcategory(
            query=query,
            sub_cat_list=sub_category_list
        )
        print(f'✅{cat_name} ', items.get("list"))
        result.append((category_name, category_id))
        msg = msg + "\n#{0}\n".format(query)
    for sub_cat in sub_category_list:

        sub_cat_name = sub_cat.get("name")
        sub_cat_id = sub_cat.get("id")
        if sub_cat_name:
            if query.lower() in sub_cat_name.lower():
                result.append((sub_cat_name, sub_cat_id))
                count += 1
                msg = unpacking_subcategory(
                    query=query,
                    sub_cat_list=sub_category_list
                )

                print(f'✅✅✅ {sub_cat_name}\t\t\t[{cat_name}]')
                # msg = msg + "#{0}".format(query)
    print(f"\n\n\n{msg = }\n")
    return result


def unpacking_subcategory(sub_cat_list: list, query: str = None) -> str:
    """

    :param sub_cat_list:
    :param query:
    :return:
    """
    msg = ''
    for category in sub_cat_list:
        subcategory_name = category["name"]
        if subcategory_name:
            if query in subcategory_name.lower():
                msg = msg + "{0}\n".format(category["name"])
    return msg
