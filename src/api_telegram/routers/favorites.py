from typing import Optional

from aiogram import F, filters, Router, types as t
from peewee import IntegrityError

from src.api_telegram import (
    FavoriteAction,
    FavoriteAddCBD,
    FavoriteCBD,
    FavoriteDeleteCBD,
    Navigation
)
from src.api_telegram.crud import (
    FavoriteAddManager,
    FavoriteDeleteManager,
    FavoriteListManager,
)
from src.database import exceptions

favorite = Router()


@favorite.message(filters.Command("favorite"))
@favorite.callback_query(FavoriteCBD.filter(F.action == FavoriteAction.paginate))
async def get_favorite_list(
        callback: t.CallbackQuery | t.Message,
        callback_data: Optional[FavoriteCBD] = None,
) -> None:
    """

    :param callback:
    :param callback_data:
    :return:
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
    except (exceptions.TelegramBadRequest, exceptions.CustomError) as error:
        # todo add logger and record `error`
        await callback.answer(f"⚠️ Ошибка{str(error)}", show_alert=True)


@favorite.callback_query(FavoriteAddCBD.filter(F.action == FavoriteAction.list))
@favorite.callback_query(FavoriteAddCBD.filter(F.action == FavoriteAction.detail))
async def add_favorite(
        callback: t.CallbackQuery, callback_data: FavoriteAddCBD
) -> None:
    """

    :param callback_data:
    :param callback:
    :return:
    """
    try:
        manager = FavoriteAddManager(callback_data, callback.from_user.id)
        await manager.add_to_favorites()
        added_item = await manager.get_item()
        await callback.answer(
            text="{0:.100}\n\n✅⭐️\tдобавлено в избранное".format(
                added_item.get("title")
            ),
            show_alert=True,
        )
        await callback.message.edit_media(
            media=await manager.message(),
            reply_markup=await manager.keyboard(),
        )

    except (IntegrityError, exceptions.FreeAPIExceededError) as error:
        # todo add logger and record `error`
        await callback.answer(
            show_alert=True, text="⚠️ Ошибка!\n\n{0}".format(str(error))
        )


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
        await callback.answer(text="✅️ товар удален из избранного", show_alert=True)
        await callback.message.edit_media(
            media=await manager.get_media(),
            reply_markup=await manager.get_keyboard(),
        )
    except (IntegrityError, exceptions.FreeAPIExceededError) as error:
        # todo add logger and record `error`
        await callback.answer(text=f"⚠️ Ошибка\n{str(error)}", show_alert=True)
