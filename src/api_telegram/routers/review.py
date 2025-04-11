from aiogram import F, Router
from aiogram import types as t

from src.api_telegram import ReviewAction, ReviewCBD, crud
from src.database.exceptions import CustomError

review = Router()


@review.callback_query(ReviewCBD.filter(F.action == ReviewAction.first))
@review.callback_query(ReviewCBD.filter(F.action == ReviewAction.paginate))
async def get_review_list(callback: t.CallbackQuery, callback_data: ReviewCBD):
    try:
        manager = crud.ReviewManager(callback_data, callback.from_user.id)
        await callback.message.edit_media(
            media=await manager.get_media(),
            reply_markup=await manager.get_keyboard(),
        )
    except CustomError as error:
        await callback.answer(text=f"⚠️ Ошибка\n{str(error)}", show_alert=True)
