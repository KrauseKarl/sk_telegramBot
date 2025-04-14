from aiogram import F, Router
from aiogram.types import CallbackQuery
from aiogram.utils.chat_action import ChatActionSender

from src.api_telegram import DetailAction, DetailCBD, ImageCBD, ImagesAction
from src.api_telegram.crud.details import DetailManager
from src.api_telegram.crud.images import ImageManager
from src.core.bot import bot
from src.database import exceptions
from src.logger import logger as log

detail = Router()


@detail.callback_query(DetailCBD.filter(F.action == DetailAction.go_view))
@detail.callback_query(DetailCBD.filter(F.action == DetailAction.back_detail))
async def get_item_detail(callback: CallbackQuery, callback_data: DetailCBD) -> None:
    try:
        chat_id = callback.message.chat.id
        async with ChatActionSender.upload_photo(
            bot=bot, chat_id=chat_id, interval=1.0
        ):
            await callback.answer()
            manage = DetailManager(callback_data, callback.from_user.id)
            await callback.message.edit_media(
                media=await manage.get_media(),
                reply_markup=await manage.get_keyboard(),
            )
    except (exceptions.CustomError, exceptions.FreeAPIExceededError) as error:
        msg = "{0:.150}".format(str(error))
        log.error_log.error(msg)
        await callback.answer(text=f"⚠️ Ошибка\n{msg}", show_alert=True)


@detail.callback_query(ImageCBD.filter(F.action == ImagesAction.images))
@detail.callback_query(ImageCBD.filter(F.action == ImagesAction.paginate))
async def get_images(callback: CallbackQuery, callback_data: ImageCBD):
    try:
        chat_id = callback.message.chat.id
        async with ChatActionSender.upload_photo(
            bot=bot, chat_id=chat_id, interval=1.0
        ):
            manager = ImageManager(callback_data, callback.from_user.id)
            await callback.message.edit_media(
                media=await manager.get_media(),
                reply_markup=await manager.get_keyboard(),
            )
    except (exceptions.CustomError, exceptions.FreeAPIExceededError) as error:
        msg = "{0:.150}".format(str(error))
        log.error_log.error(msg)
        await callback.answer(text=f"⚠️ Ошибка\n{msg}", show_alert=True)
