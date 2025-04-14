from aiogram import F, Router
from aiogram import types as t
from aiogram.utils.chat_action import ChatActionSender

from src.api_telegram import ReviewAction, ReviewCBD, crud
from src.core.bot import bot
from src.database.exceptions import CustomError
from src.logger import logger as log

review = Router()


@review.callback_query(ReviewCBD.filter(F.action == ReviewAction.first))
@review.callback_query(ReviewCBD.filter(F.action == ReviewAction.paginate))
async def get_review_list(callback: t.CallbackQuery, callback_data: ReviewCBD) -> None:
    """
    Возвращает список комментариев к товару.

    :param callback: CallbackQuery
    :param callback_data: ReviewCBD
    :return: None
    """
    try:
        chat_id = callback.message.chat.id
        async with ChatActionSender.upload_photo(
            bot=bot, chat_id=chat_id, interval=1.0
        ):
            manager = crud.ReviewManager(callback_data, callback.from_user.id)
            await callback.message.edit_media(
                media=await manager.get_media(),
                reply_markup=await manager.get_keyboard(),
            )
    except CustomError as error:
        msg = "{0:.150}".format(str(error))
        log.error_log.error(msg)
        await callback.answer(text=f"⚠️ Ошибка\n{msg}", show_alert=True)
