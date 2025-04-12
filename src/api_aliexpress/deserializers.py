import emoji

from src.api_redis.handlers import RedisHandler
from src.core.config import FLAGS, MESSAGE_LIMIT

redis_handler = RedisHandler()


class DeserializedHandler:
    @staticmethod
    async def item_list(params):
        item_data = params.get("item", {})
        sku = item_data.get("sku", {}).get("def", {})
        item_id = item_data.get("itemId")
        title = item_data.get("title", "N/A")
        price = sku.get("promotionPrice", "N/A")
        sales = item_data.get("sales", "N/A")
        url = item_data.get("itemUrl", "N/A")
        page = params.get("page", "N/A")
        total_pages = params.get("total_pages", "N/A")
        api_page = params.get("api_page", "N/A")
        img = ":".join(["https", params.get("item").get("image")])
        msg = (
            f"<b>{title[:50]}</b>\n"
            f"💰\t\tцена:\t\t<b>{price}</b> RUB\n"
            f"👀\t\tзаказы:\t\t<b>{sales}</b>\n"
            f"🌐\t\t{url}\n\n"
            f"<b>{page}</b> из {total_pages} стр. {api_page}\t"
        )
        return msg, img, item_id

    @staticmethod
    async def item_detail(params):
        item_data = params.get("result").get("item")
        msg = ""
        title = item_data.get("title", "N/A")
        item_url = ":".join(["https", item_data.get("itemUrl")])
        properties = item_data.get("properties").get("list")[:15]
        prom_price = item_data.get("sku").get("base")[0]["promotionPrice"]

        try:
            prop = params["result"]["item"]["sku"]["props"]
            if prop[0].get("name") in ["Size", "Размер"] and prop[0].get(
                "name"
            ) not in ["Color", "Цвет"]:
                size = prop[0]["values"]
            else:
                size = prop[1]["values"]
        except IndexError:
            size = None

        reviews = params.get("result").get("reviews").get("count", "N/A")
        average_star = params.get("result").get("reviews").get("averageStar", "N/A")
        delivery = params["result"]["delivery"]
        shipping_out_days = delivery.get("shippingOutDays", "N/A")
        weight = delivery.get("packageDetail").get("weight", "N/A")
        length = delivery.get("packageDetail").get("height", "N/A")
        width = delivery.get("packageDetail").get("width", "N/A")
        height = delivery.get("packageDetail").get("height", "N/A")
        store_title = params.get("result").get("seller").get("storeTitle", "N/A")
        store_url = ":".join(["https", params["result"]["seller"]["storeUrl"]])

        msg += "{0}\n\n{1:.150}\n\n".format(item_url, title)
        msg += "💰\tЦена: {0} руб.\n\n".format(prom_price)
        try:
            msg += "<u>Размеры:</u> ".upper()
            for s in size:
                msg += "\t {0},".format(s["name"])
        except Exception as err:
            print("❌ERROR:[Размеры]", err)
        try:
            msg += "\n<u>характеристики:</u>\n".upper()
            for prop in properties:
                msg += "\t- {0}: {1}\n".format(prop["name"], prop["value"])
        except Exception as err:
            print("❌ERROR:[характеристики] ", err)
        try:
            msg += "\n📈 Продажи: {0}\n".format(reviews)
            msg += "⭐️ Рейтинг: {0}\n".format(average_star)
        except Exception as err:
            print("❌ERROR: ", err)
        try:
            msg += "\n🚚 Доставка: ".upper()
            msg += "{0} дн.\n".format(shipping_out_days)
            msg += "- вес: {0} кг\n".format(weight)
            msg += "\t- длина:  {0} см\n".format(length)
            msg += "\t- ширина: {0} см\n".format(width)
            msg += "\t- высота: {0} см\n".format(height)
            msg += "\n🏪 Продавец:\n".upper()
            msg += "\t{0}\n\t{1}\n".format(store_title, store_url)
        except Exception as err:
            print("❌ERROR: ", err)
        return msg[: (MESSAGE_LIMIT - 1)] if len(msg) > MESSAGE_LIMIT else msg

    @staticmethod
    async def item_for_db(params, user_id):
        obj = params["result"]["item"]
        reviews = params["result"]["reviews"]
        item_data = dict(
            user=user_id,
            product_id=obj.get("itemId"),
            title=obj.get("title", "N/A"),
            price=obj.get("sku").get("base")[0].get("promotionPrice", "N/A"),
            reviews=reviews.get("count", "N/A"),
            stars=reviews.get("averageStar", "N/A"),
            url=":".join(["https", obj.get("itemUrl", "N/A")]),
        )
        try:
            item_data["image"] = ":".join(["https", obj["images"][0]])
        except (KeyError, IndexError):
            item_data["image"] = None
        return item_data

    @staticmethod
    async def history(obj, page: str, len_list: int) -> str:
        """

        :param len_list:
        :param page:
        :param obj:
        :return:
        """
        msg = "📅 {0}\t".format(obj.date.strftime("%d %b %Y"))
        msg += "🕐 {0}\n".format(obj.date.strftime("%H:%M:%S"))
        msg += "✅ {:.30}\n".format(obj.title) if obj.title else ""
        msg += "🟠 {0} RUB\n".format(obj.price) if obj.price else ""
        msg += "👀 промоторы {0}\n".format(obj.reviews) if obj.reviews else ""
        msg += "⭐️рейтинг {0}\n".format(obj.stars) if obj.stars else ""
        msg += "{0}\n\n".format(obj.url.split("//")[1]) if obj.url else ""
        msg += "{0} из {1}".format(page, len_list)

        return msg

    @staticmethod
    async def favorite(obj, page: str | int, total_page: int) -> str:
        """

        :param total_page:
        :param page:
        :param obj:
        :return:
        """
        msg = "📅\t{0}\n".format(obj.date.strftime("%d %b %Y"))
        msg += "🕐\t{0}\n".format(obj.date.strftime("%H:%M:%S"))
        msg += "🆔\t<u>id</u>:\t{0}\n".format(obj.product_id)
        msg += "✅\t{:.50}\n".format(obj.title)
        msg += "🟠\t<i>цена</i>:\t{0}\tRUB\n".format(obj.price)
        msg += "👀\t<i>просмотров</i>:\t{0}\n\n".format(obj.reviews)
        msg += "⭐️\t<i>рейтинг</i>:\t{0}\n".format(obj.stars)
        msg += "{0}\n".format(obj.url.split("//")[1])
        msg += "\n{0} из {1}".format(page, total_page)
        return msg

    @staticmethod
    async def monitor(obj, page: int, total_page: int) -> str:
        """

        :param total_page:
        :param page:
        :param obj:
        :return:
        """

        msg = "📅\t{0}\n".format(obj.date.strftime("%d %b %Y"))
        msg += "🕐\t{0}\n".format(obj.date.strftime("%H:%M:%S"))
        msg += "🆔\t<u>id</u>:\t{0}\n".format(obj.product_id)
        msg += "✅\t{:.50}\n".format(obj.title)
        msg += "🟠\t<i>цена</i>:\t{0}\tRUB\n".format(obj.price)
        msg += "🎯\t<i>цель</i>:\t{0}\tRUB\n".format(obj.target if obj.target else "❌")
        if obj.target is not None and float(obj.price) <= float(obj.target):
            msg += "\n✅ Заданная цена достигнута\n\n"
        msg += "\n{0} из {1}".format(page, total_page)
        return msg

    @staticmethod
    async def reviews(obj, page: str, total_page: int) -> str:
        obj_review = obj.get("review")
        dtime = obj_review.get("reviewDate")
        stars = obj_review.get("reviewStarts")
        item_title = obj_review.get("itemSpecInfo")
        text = obj_review.get("translation").get("reviewContent", "no comment")
        flag = FLAGS[obj.get("buyer").get("buyerCountry", "pirate_flag")].replace(
            " ", "_"
        )
        country = FLAGS[obj.get("buyer").get("buyerCountry")]

        msg = "{0}\n".format("⭐️" * stars)
        msg += "{0}\n\n".format(dtime)
        msg += "<i>{0:.200}</i>\n\n".format(text)
        msg += "📦 item: {0:.50}\n".format(item_title)
        msg += "👤 name: {0}\n".format(obj["buyer"]["buyerTitle"])
        msg += emoji.emojize(":{0}: {1}".format(flag, country))
        msg += "\n\n<b>{0}</b> из {1}\t".format(page, total_page)

        return msg
