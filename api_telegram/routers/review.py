from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm import state

from api_aliexpress.request import *
from api_redis.handlers import *
from api_telegram.callback_data import *
from api_telegram.crud.reviews import get_review_image
from api_telegram.keyboards import *
from api_telegram.paginations import pagination_review_kb
from core.config import conf
from database.paginator import *
from utils.cache_key import get_extra_cache_key
from utils.media import *
from utils.message_info import *

review = Router()
redis_handler = RedisHandler()


@review.callback_query(ReviewCBD.filter(F.action == ReviewAction.first))
@review.callback_query(ReviewCBD.filter(F.action == ReviewAction.paginate))
async def request_review(callback: CallbackQuery, callback_data: ReviewCBD):
    # try:
    item_id = callback_data.item_id
    key = callback_data.key
    api_page = int(callback_data.api_page)
    sub_page = callback_data.sub_page
    # cache_key = CacheKeyExtended(
    #     key=key,
    #     api_page=api_page,
    #     extra='review',
    #     sub_page=extra_page
    # ).pack()
    cache_key = await get_extra_cache_key(callback_data, 'review')
    review_list = await redis_handler.get_data(cache_key)

    if review_list is None:
        data = dict(
            url=config.URL_API_REVIEW,
            page=str(api_page),
            itemId=item_id,
            sort="latest",
            filters="allReviews"
        )
        response = await request_api_review(data)
        review_list = response.get('result').get('resultList', None)
    if review_list is not None:
        await redis_handler.set_data(key=cache_key, value=review_list)
        paginator = Paginator(array=review_list, page=int(sub_page))
        reviews = paginator.get_page()[0]
        msg = await create_review_tg_answer(reviews, sub_page, paginator.len)
        photo = await get_review_image(reviews, msg)
        kb = await pagination_review_kb(paginator.len, callback_data)

    else:
        kb = BasePaginationBtn()
        kb.add_button(kb.btn_text('menu'))
        photo = await get_review_image()

    await callback.message.edit_media(media=photo, reply_markup=kb.create_kb())

# except Exception as error:
#     print(str(error))
#     await callback.answer(text=f'⚠️ {str(error)}')
