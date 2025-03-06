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
from utils.media import *
from utils.message_info import *

review = Router()


@review.callback_query(ReviewCBD.filter(F.action.in_({RevAction.first, RevAction.page})))
async def request_review(callback: CallbackQuery, callback_data: ReviewCBD):
    try:
        item_id = callback_data.item_id
        key = callback_data.key
        api_page = int(callback_data.api_page)
        extra_page = callback_data.review_page

        cache_key = CacheKey(key=key, api_page=api_page, extra='review').pack()
        review_list = await redis_get_data_from_cache(cache_key)

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
            await redis_set_data_to_cache(key=cache_key, value=review_list)
            paginator = Paginator(array=review_list, page=int(extra_page))
            reviews = paginator.get_page()[0]
            msg = await create_review_tg_answer(reviews, extra_page, paginator.len)
            photo = await get_review_image(reviews, msg)
        else:
            photo = await get_review_image()
        media = await get_fs_input_hero_image('not_found')
        photo = types.InputMediaPhoto(media=media, caption=msg)
        kb = await pagination_review_kb(review_list, callback_data)
        await callback.message.edit_media(media=photo, reply_markup=kb.create_kb())
    except Exception as error:
        print(str(error))
        await callback.answer(text=f'⚠️ error review')
