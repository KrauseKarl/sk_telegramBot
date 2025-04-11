from aiogram import F, Router
from aiogram.types import CallbackQuery

from src.api_telegram import DetailAction, ImageCBD, ImagesAction, DetailCBD
from src.api_telegram.crud.details import DetailManager
from src.api_telegram.crud.images import ImageManager
from src.database import exceptions

detail = Router()


@detail.callback_query(DetailCBD.filter(F.action == DetailAction.go_view))
@detail.callback_query(DetailCBD.filter(F.action == DetailAction.back_detail))
async def get_item_detail(callback: CallbackQuery, callback_data: DetailCBD) -> None:
    try:
        await callback.answer()
        manage = DetailManager(callback_data, callback.from_user.id)
        await callback.message.edit_media(
            media=await manage.get_media(),
            reply_markup=await manage.get_keyboard(),
        )
    except exceptions.FreeAPIExceededError as error:
        await callback.answer(text=f"⚠️ Ошибка\n{str(error)}", show_alert=True)
    except exceptions.CustomError as error:
        await callback.answer(text=f"⚠️ Ошибка\n{str(error)}", show_alert=True)


@detail.callback_query(ImageCBD.filter(F.action == ImagesAction.images))
@detail.callback_query(ImageCBD.filter(F.action == ImagesAction.paginate))
async def get_images(callback: CallbackQuery, callback_data: ImageCBD):
    try:
        manager = ImageManager(callback_data, callback.from_user.id)
        await callback.message.edit_media(
            media=await manager.get_media(),
            reply_markup=await manager.get_keyboard(),
        )
    except exceptions.FreeAPIExceededError as error:
        await callback.answer(text=f"⚠️ Ошибка\n{str(error)}", show_alert=True)
    except exceptions.CustomError as error:
        await callback.answer(text=f"⚠️ Ошибка\n{str(error)}", show_alert=True)
