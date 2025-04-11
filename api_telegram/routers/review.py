from aiogram import Router, F, types as t

from api_redis.handlers import RedisHandler
from api_telegram import ReviewCBD, ReviewAction
from api_telegram.crud import ReviewManager

review = Router()
redis_handler = RedisHandler()


@review.callback_query(ReviewCBD.filter(F.action == ReviewAction.first))
@review.callback_query(ReviewCBD.filter(F.action == ReviewAction.paginate))
async def get_review_list(callback: t.CallbackQuery, callback_data: ReviewCBD):
    try:
        manager = ReviewManager(callback_data, callback.from_user.id)
        await callback.message.edit_media(
            media=await manager.get_media(),
            reply_markup=await manager.get_keyboard())
    except Exception as error:
        await callback.answer(
            text=f"⚠️ Ошибка\n{str(error)}",
            show_alert=True
        )
