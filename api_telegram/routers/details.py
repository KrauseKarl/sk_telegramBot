from aiogram import F, Router
from aiogram.types import CallbackQuery

from api_telegram import DetailAction, ImageCBD, ImagesAction
from api_telegram.crud.image import ImageManager
from api_telegram.crud.detail import DetailManager
from api_aliexpress.deserializers import *
from api_telegram.keyboard.builders import kbm
from database.exceptions import *
from utils.message_info import *

detail = Router()


@detail.callback_query(DetailCBD.filter(F.action == DetailAction.go_view))
@detail.callback_query(DetailCBD.filter(F.action == DetailAction.back_detail))
async def get_item_detail(callback: CallbackQuery, callback_data: DetailCBD) -> None:
    try:
        await callback.answer()
        manage = DetailManager(callback_data, callback.from_user.id)
        await callback.message.edit_media(
            media=await manage.get_media(),
            reply_markup=await manage.get_keyboard()
        )
    except FreeAPIExceededError as error:
        await callback.answer( text="⚠️ ОШИБКА\n\n{0}".format(error), show_alert=True)
    except CustomError as error:
        msg, photo = await get_error_answer_photo(error)
        await callback.message.answer_photo(
            photo=photo,
            caption=msg,
            reply_markup=await kbm.menu()
        )


@detail.callback_query(ImageCBD.filter(F.action == ImagesAction.images))
@detail.callback_query(ImageCBD.filter(F.action == ImagesAction.paginate))
async def get_images(callback: CallbackQuery, callback_data: ImageCBD):
    try:
        manager = ImageManager(callback_data, callback.from_user.id)
        await callback.message.edit_media(
            media=await manager.get_media(),
            reply_markup=await manager.get_keyboard()
        )
    except FreeAPIExceededError as error:
        await callback.answer(text="⚠️ ОШИБКА\n\n{0}".format(error), show_alert=True)
    except CustomError as error:
        msg, photo = await get_error_answer_photo(error)
        await callback.message.answer_photo(
            photo=photo,
            caption=msg,
            reply_markup=await kbm.menu()
        )

