import json
import os
import emoji
import httpx
from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from aiogram.fsm import state

from api_aliexpress.request import *
from api_redis.handlers import *
from api_telegram.callback_data import *
from api_telegram.keyboards import *
from core import *
from core.config import conf
from database.paginator import *
from utils.media import *
from utils.message_info import *

review = Router()


class Review(state.StatesGroup):
    product = state.State()


async def save_data_json_local(data, item_id: str = None, folder: str = None):
    file_name = "{0}.json".format(item_id.lower())
    file_path = os.path.join(
        config.BASE_DIR,
        "_json_example",
        folder,
        file_name
    )
    with open(file_path, "w") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)


# "/item_review?
# itemId        =1005006898150255
# page          =1
# sort          =latest
# filter        =allReviews

async def request_api_review(
        url: str = None,
        page: str = None,
        item_id: str = None,
        sort: str = None,
        filter: str = None

) -> dict:

    full_url = "/".join([conf.base_url, url])
    if item_id:
        conf.querystring["itemId"] = item_id
    if sort:
        conf.querystring["sort"] = sort
    if page:
        conf.querystring["page"] = page
    if filter:
        conf.querystring["filter"] = filter

    async with httpx.AsyncClient() as client:
        response = await client.get(
            url=full_url,
            headers=conf.headers,
            params=conf.querystring
        )
    result = response.json()
    if item_id:
        await save_data_json(data=result, item_id=item_id, folder=REVIEW_FAKE_FOLDER)

    return result


@review.callback_query(ReviewCBD.filter(F.action == RevAction.first))
async def request_review(callback: CallbackQuery, callback_data: ReviewCBD):
    item_id = callback_data.item_id
    # comment_list = await request_api_review_fake(item_id)
    key = callback_data.key
    page = int(callback_data.page)
    api_page = int(callback_data.api_page)
    cache_key = CacheKey(key=key, api_page=api_page, extra='review').pack()
    review_list_cache = await redis_get_data_from_cache(cache_key)

    if review_list_cache is None:
        response = await request_api_review(
            url=config.URL_API_REVIEW,
            page=str(api_page),
            item_id=item_id,
            sort="latest",
            filter="allReviews"
        )
        review_list_cache = response['result']['resultList']
        await redis_set_data_to_cache(key=cache_key, value=review_list_cache)

    print(f"⬜️REVIEW DATA FROM 🟩 CACHE ")
    if api_page == 0 or page > len(review_list_cache):
        print(f"⬜️️REVIEW DATA FROM 🟥 REQUEST")
        api_page += 1
        ########################################################################
        if config.FAKE_MODE:
            my_file = Path(
                os.path.join(
                    config.BASE_DIR,
                    FAKE_MAIN_FOLDER,
                    REVIEW_FAKE_FOLDER,
                    "review_{0}.json".format(item_id)
                )
            )
            if my_file.is_file():
                print('request from 🟩 FILE')
                response = await request_api_review_fake(item_id=item_id)
            else:
                response = await request_api_review(
                    url=config.URL_API_REVIEW,
                    page=str(api_page),
                    item_id=item_id,
                    sort="latest",
                    filter="allReviews"
                )
        else:
            response = await request_api_review(
                url=config.URL_API_REVIEW,
                page=str(api_page),
                item_id=item_id,
                sort="latest",
                filter="allReviews"
            )
        ########################################################################
        review_list_cache = response['result']['resultList']
        cache_key = CacheKey(key=key, api_page=api_page, extra='review').pack()
        page = 1
        cache_data = await redis_get_data_from_cache(cache_key)
        if cache_data is None:
            await redis_set_data_to_cache(key=cache_key, value=review_list_cache)

    paginator = Paginator(array=review_list_cache, page=page)
    comment = paginator.get_page()[0]
    msg = await create_review_tg_answer(comment, page, api_page, paginator.len)
    kb = KeyBoardFactory()
    btn = CommentPaginationBtn(item_id)

    if paginator.len > 1:
        # if navigate == RevPagination.first:
        kb.add_button({"След. ➡️": btn.next_bt(page)}).add_markup(1)
        #
        # elif navigate == FavPagination.next:
        #     kb.add_button({"⬅️ Пред.": btn.prev_bt(page)}).add_markup(1)
        #     if page < len_data:
        #         kb.add_button({"След. ➡️": btn.next_bt(page)}).update_markup(2)
        #
        # elif navigate == FavPagination.prev:
        #     kb.add_button({"След. ➡️": btn.next_bt(page)}).add_markup(1)
        #     if page > 1:
        #         kb.add_button({"⬅️ Пред.": btn.prev_bt(page)}).update_markup(2)
    back_to_list = DetailCBD(
        action=DetailAction.back,
        item_id=callback_data.item_id,
        key=callback_data.key,
        api_page=callback_data.api_page,
        page=callback_data.page,
        next=callback_data.next,
        prev=callback_data.prev,
        first=callback_data.first,
        last=callback_data.last,
    ).pack()
    buttons = [{"🏠 назад": back_to_list}]
    kb.add_buttons(buttons).add_markup(1)
    media = await get_fs_input_hero_image('result')
    photo = types.InputMediaPhoto(media=media, caption=msg)
    await callback.message.edit_media(media=photo, reply_markup=kb.create_kb())

# @review.callback_query(F.data.startswith("review"))
# async def request_review_message(message: CallbackQuery, state: FSMContext) -> None:
#     await state.clear()
#     await state.set_state(Review.product)
#     await message.message.answer('💬💬💬 Введите артикул товара')
#
#
# @review.message(Review.product)
# async def request_product_name(message: Message, state: FSMContext) -> None:
#     await state.update_data(product=message.text)
#     # response = await request_api_review(
#     #     item_id=message.text,
#     #     sort="latest",
#     #     url=config.URL_API_REVIEW,
#     #     page='1',
#     #     filter="allReviews"
#     # )
#     response = await request_api_review_fake(item_id=message.text)
#     reviews = response['result']['resultList'][:20]
#
#     for r in reviews:
#         dtime = r['review']['reviewDate']
#         stars = r['review']['reviewStarts']
#         item_title = r['review']['itemSpecInfo']
#         review_text = r.get('review').get('translation').get('reviewContent', 'no comment')
#         msg = "{0}\n".format("⭐️" * stars)
#         msg += '{0}\n'.format(dtime)
#         msg += "<i>{0:.200}</i>\n\n".format(review_text)
#         msg += "📦 item: {0:.50}\n".format(item_title)
#         msg += "👤 name: {0}\n".format(r['buyer']['buyerTitle'])
#         try:
#             country = config.FLAGS[r['buyer']['buyerCountry']].replace(" ", "_")
#             country_name = config.FLAGS[r['buyer']['buyerCountry']]
#             print(country, country_name)
#         except KeyError:
#             country = "pirate_flag"
#             country_name = r['buyer']['buyerCountry']
#
#         msg += emoji.emojize(":{0}: {1}".format(country, country_name))
#
#         await message.answer(msg)
#
#     # result
#     #     "resultList": [
#     #       {
#     #         "review": {
#     #           "reviewId": 60088804112413800,
#     #           "reviewDate": "25 фев 2025",
#     #           "reviewContent": "Fits true. Nice material ",
#     #           "reviewAdditional": null,
#     #           "reviewStarts": 5,
#     #           "reviewImages": null,
#     #           "reviewAnonymous": false,
#     #           "reviewHelpfulYes": 0,
#     #           "reviewHelpfulNo": 0,
#     #           "itemSpecInfo": "Color:Black Long Sleeve 3 Size:L ",
#     #           "itemLogistics": "AliExpress Standard Shipping",
#     #           "translation": {
#     #             "reviewContent": "Подходит правда. Хороший материал",
#     #             "reviewLanguage": "ru"
#     #           }
#     #         },
#     #         "buyer": {
#     #           "buyerTitle": "L***d",
#     #           "buyerGender": null,
#     #           "buyerCountry": "CA",
#     #           "buyerImage": null
#     #         }
#     #       },
