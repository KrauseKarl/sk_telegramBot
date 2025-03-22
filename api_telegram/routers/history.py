from aiogram import F, Router, types as t
from aiogram.filters import Command

from api_telegram.crud.histories import *
from api_telegram.keyboard.builders import kbm
from api_telegram.callback_data import HistoryAction, HistoryCBD
from database.exceptions import *
from database.orm import *
from utils.media import *
from utils.message_info import *

history = Router()


# HISTORY #############################################################################################################
@history.message(Command("history"))
@history.callback_query(HistoryCBD.filter(F.action == HistoryAction.first))
@history.callback_query(HistoryCBD.filter(F.action == HistoryAction.paginate))
async def history_page(
        callback: t.CallbackQuery | t.Message,
        callback_data: Optional[HistoryCBD] = None
) -> None:
    """

    :param callback_data:
    :param callback:
    :return:
    """
    try:
        if callback_data is None:
            callback_data = HistoryCBD(
                action=HistoryAction.first,
                navigate=Navigation.first
            )
        manager = HistoryManager(callback_data, callback.from_user.id)
        if isinstance(callback, t.Message):
            await callback.answer_photo(
                photo=await manager.get_photo(),
                caption=await manager.get_msg(),
                reply_markup=await manager.get_keyboard()
            )
        else:
            await callback.message.edit_media(
                media=await manager.get_media(),
                reply_markup=await manager.get_keyboard()
            )
    except CustomError as error:
        msg, photo = await get_error_answer_photo(error)
        await callback.message.answer_photo(
            photo=photo,
            caption=msg,
            reply_markup=await kbm.menu()
        )
