from aiogram import Router, F
from aiogram.types import CallbackQuery

from api_redis.handlers import *
from api_telegram import ReviewCBD, ReviewAction
from api_telegram.crud.reviews import ReviewManager
from utils.media import *
from utils.message_info import *

review = Router()
redis_handler = RedisHandler()


@review.callback_query(ReviewCBD.filter(F.action == ReviewAction.first))
@review.callback_query(ReviewCBD.filter(F.action == ReviewAction.paginate))
async def request_review(callback: CallbackQuery, callback_data: ReviewCBD):
    try:
        manager = ReviewManager(callback_data, callback.from_user.id)
        await callback.message.edit_media(
            media=await manager.get_media(),
            reply_markup=await manager.get_keyboard())
    except Exception as error:
        await callback.answer(text=f'⚠️ {str(error)}')
