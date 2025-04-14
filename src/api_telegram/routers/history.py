from typing import Optional

from aiogram import F, Router, filters
from aiogram import types as t

from src.api_telegram import HistoryAction, HistoryCBD, Navigation
from src.api_telegram.crud import HistoryManager
from src.database import exceptions
from src.logger import logger as log

history = Router()


@history.message(filters.Command("history"))
@history.callback_query(HistoryCBD.filter(F.action == HistoryAction.first))
@history.callback_query(HistoryCBD.filter(F.action == HistoryAction.paginate))
async def history_list(
    callback: t.CallbackQuery | t.Message,
    callback_data: Optional[HistoryCBD] = None,
) -> None:
    """
    Возвращает список записей в историю просмотров пользователя.

    :param callback_data: HistoryCBD
    :param callback: CallbackQuery | Message
    :return: None
    """
    try:
        if callback_data is None:
            callback_data = HistoryCBD(
                action=HistoryAction.first, navigate=Navigation.first
            )
        manager = HistoryManager(callback_data, callback.from_user.id)
        if isinstance(callback, t.Message):
            await callback.answer_photo(
                photo=await manager.get_photo(),
                caption=await manager.get_msg(),
                reply_markup=await manager.get_keyboard(),
            )
        else:
            await callback.message.edit_media(
                media=await manager.get_media(),
                reply_markup=await manager.get_keyboard(),
            )
    except exceptions.CustomError as error:
        msg = "{0:.150}".format(str(error))
        log.error_log.error(msg)
        await callback.answer(text=f"⚠️ Ошибка\n{msg}", show_alert=True)
