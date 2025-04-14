from typing import Optional

from aiogram import F, Router, exceptions, filters
from aiogram import types as t
from aiogram.utils.chat_action import ChatActionSender
from peewee import IntegrityError

from src.api_telegram import (
    FavoriteAction,
    FavoriteAddCBD,
    FavoriteCBD,
    FavoriteDeleteCBD,
    Navigation,
)
from src.api_telegram.crud import (
    FavoriteAddManager,
    FavoriteDeleteManager,
    FavoriteListManager,
)
from src.core.bot import bot
from src.database import exceptions as expt
from src.logger import logger as log

favorite = Router()


@favorite.message(filters.Command("favorite"))
@favorite.callback_query(FavoriteCBD.filter(F.action == FavoriteAction.paginate))
async def get_favorite_list(
    callback: t.CallbackQuery | t.Message,
    callback_data: Optional[FavoriteCBD] = None,
) -> None:
    """
    Возвращает список избранных товаров.

    :param callback: CallbackQuery | Message,
    :param callback_data: FavoriteCBD
    :return: None
    """

    try:
        if callback_data is None:
            callback_data = FavoriteCBD(
                action=FavoriteAction.paginate, navigate=Navigation.first
            )
        manager = FavoriteListManager(callback_data, callback.from_user.id)
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
    except (exceptions.TelegramBadRequest, expt.CustomError) as error:
        msg = "{0:.150}".format(str(error))
        log.error_log.error(msg)
        await callback.answer(text=f"⚠️ Ошибка\n{msg}", show_alert=True)


@favorite.callback_query(FavoriteAddCBD.filter(F.action == FavoriteAction.list))
@favorite.callback_query(FavoriteAddCBD.filter(F.action == FavoriteAction.detail))
async def add_favorite(
    callback: t.CallbackQuery, callback_data: FavoriteAddCBD
) -> None:
    """
    Добавляет товар в `избранное`.

    :param callback_data: FavoriteAddCBD
    :param callback: CallbackQuery
    :return: None
    """
    try:
        chat_id = callback.message.chat.id
        async with ChatActionSender.upload_photo(
            bot=bot, chat_id=chat_id, interval=1.0
        ):
            manager = FavoriteAddManager(callback_data, callback.from_user.id)
            await manager.add_to_favorites()
            added_item = await manager.get_item()
            msg = "{0:.100}\n\n✅⭐️\tдобавлено в избранное".format(
                added_item.get("title")
            )
            log.info_log.info(msg)
            await callback.answer(text=msg, show_alert=True)
            await callback.message.edit_media(
                media=await manager.message(),
                reply_markup=await manager.keyboard(),
            )

    except (IntegrityError, expt.CustomError) as error:
        msg = "{0:.150}".format(str(error))
        log.error_log.error(msg)
        await callback.answer(text=f"⚠️ Ошибка\n{msg}", show_alert=True)


@favorite.callback_query(FavoriteDeleteCBD.filter(F.action == FavoriteAction.delete))
async def delete_favorite(
    callback: t.CallbackQuery, callback_data: FavoriteDeleteCBD
) -> None:
    """

    :param callback:
    :param callback_data:
    :return:
    """
    try:
        manager = FavoriteDeleteManager(callback_data, callback.from_user.id)
        await manager.delete_from_favorites()
        msg = "🗑 товар удален из избранного"
        log.info_log.info(msg)
        await callback.answer(text=msg, show_alert=True)
        await callback.message.edit_media(
            media=await manager.get_media(),
            reply_markup=await manager.get_keyboard(),
        )
    except (IntegrityError, expt.CustomError) as error:
        msg = "{0:.150}".format(str(error))
        log.error_log.error(msg)
        await callback.answer(text=f"⚠️ Ошибка\n{msg}", show_alert=True)
