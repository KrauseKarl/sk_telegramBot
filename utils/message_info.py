import emoji
from aiogram import types

from database import orm_get_favorite
from database.paginator import *


async def create_tg_answer(params):
    item = params.get('item', {})
    sku = item.get("sku", {}).get("def", {})

    item_id = item.get("itemId")
    title = item.get("title", "")
    price = sku.get("promotionPrice", "N/A")
    sales = item.get("sales", "N/A")
    url = item.get("itemUrl", "")
    page = params.get("page", "N/A")
    total_pages = params.get("total_pages", "N/A")
    api_page = params.get("api_page", "N/A")
    img = ":".join(["https", params.get('item').get("image")])

    msg = (
        f"<b>{title[:50]}</b>\n"
        f"💰\t\tцена:\t\t<b>{price}</b> RUB\n"
        f"👀\t\tзаказы:\t\t<b>{sales}</b>\n"
        f"🌐\t\t{url}\n\n"
        f"<b>{page}</b> из {total_pages} стр. {api_page}\t"
    )

    is_favorite = await orm_get_favorite(item_id)
    if is_favorite:
        msg += "👍\tв избранном"

    return types.InputMediaPhoto(media=img, caption=msg)


async def refresh_tg_answer(item, item_id, page, api_page, total_pages):
    msg = "<b>{0:.50}</b>\n".format(item["title"])
    msg += "💰\t\tцена:\t\t<b>{0}</b> RUB\n".format(item["price"])
    msg += "👀\t\tзаказы:\t\t<b>{0}</b>\n".format(item["reviews"])
    msg += "🌐\t\t{0}\n\n".format(item["url"])
    msg += "<b>{0}</b> из {1} стр. {2}\t".format(page, total_pages, api_page)
    is_favorite = await orm_get_favorite(item_id)
    if is_favorite:
        msg += "👍\tв избранном"
    return types.InputMediaPhoto(media=item["image"], caption=msg)


async def create_review_tg_answer(obj, page, total_pages):
    dtime = obj.get('review').get('reviewDate')
    stars = obj.get('review').get('reviewStarts')
    item_title = obj['review']['itemSpecInfo']
    review_text = obj.get('review').get('translation').get('reviewContent', 'no comment')
    msg = "{0}\n".format("⭐️" * stars)
    msg += '{0}\n\n'.format(dtime)
    msg += "<i>{0:.200}</i>\n\n".format(review_text)
    msg += "📦 item: {0:.50}\n".format(item_title)
    msg += "👤 name: {0}\n".format(obj['buyer']['buyerTitle'])
    try:
        country = FLAGS[obj['buyer']['buyerCountry']].replace(" ", "_")
        country_name = FLAGS[obj['buyer']['buyerCountry']]
    except KeyError:
        country = "pirate_flag"
        country_name = obj['buyer']['buyerCountry']

    msg += emoji.emojize(":{0}: {1}".format(country, country_name))
    msg += "\n\n<b>{0}</b> из {1}\t".format(page, total_pages)

    return msg
