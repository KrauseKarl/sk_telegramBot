from aiogram import F, Router, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton
from pydantic import ValidationError

from api_telegram.crud.histories import *
from database.exceptions import *
from database.orm import *
from utils.media import *
from utils.message_info import *

history = Router()


# HISTORY #############################################################################################################
@history.message(Command("history"))
async def history_message(message: types.Message) -> None:
    """

    :param message:
    :return:
    """
    try:
        msg, kb, img = await get_history_message(message.from_user.id)
        await message.answer_photo(photo=img, caption=msg, reply_markup=kb)
    except CustomError as error:
        msg, img = await get_error_answer_photo(error)
        await message.answer_photo(
            photo=img, caption=msg, reply_markup=await menu_kb()
        )


@history.callback_query(F.data.startswith("history"))
async def history_callback(callback: types.CallbackQuery) -> None:
    """

    :param callback:
    :return:
    """
    try:
        msg, kb, img = await get_history_message(callback.from_user.id)
        img = types.InputMediaPhoto(media=img, caption=msg)
        await callback.message.edit_media(media=img, reply_markup=kb)
    except CustomError as error:
        await callback.message.edit_media(
            media=await get_error_answer_media(error),
            reply_markup=await menu_kb()
        )


@history.callback_query(F.data.startswith("page"))
async def history_page(callback: types.CallbackQuery) -> None:
    """

    :param callback:
    :return:
    """
    try:
        history_list = await orm_get_history_list(callback.from_user.id)

        # todo make func make_paginate_history_list
        page = int(callback.data.split("_")[-1])
        paginator = Paginator(history_list, page=int(page))
        history_item = paginator.get_page()[0]
        msg = await history_info(history_item)
        msg = msg + "{0} из {1}".format(page, paginator.pages)

        # todo make func kb_page_builder and remove to pagination.py
        kb = InlineKeyboardBuilder()
        if callback.data.startswith("page_next"):
            callback_previous = "page_previous_{0}".format(page - 1)
            kb.add(InlineKeyboardButton(text="◀ Пред.", callback_data=callback_previous))
            if page != paginator.pages:
                callback_next = "page_next_{0}".format(page + 1)
                kb.add(InlineKeyboardButton(text='След. ▶', callback_data=callback_next))
                # if paginator.pages > 10:
                #     callback_next = "page_next_{0}".format(page + 10)
                #     kb.add(InlineKeyboardButton(text='След. 10 ▶', data=callback_next))
        elif callback.data.startswith("page_previous"):
            if page != 1:
                callback_previous = "page_previous_{0}".format(page - 1)
                kb.add(InlineKeyboardButton(text="◀ Пред.", callback_data=callback_previous))
                # if page > 10:
                #     callback_previous = "page_previous_{0}".format(page - 10)
                #     kb.add(InlineKeyboardButton(text="◀ Пред. 10", data=callback_previous))
            callback_next = "page_next_{0}".format(page + 1)
            kb.add(InlineKeyboardButton(text='След. ▶', callback_data=callback_next))
        kb.add(InlineKeyboardButton(text='главное меню', callback_data="menu"))
        # todo make func kb_page_builder and remove to pagination.py

        try:
            img = types.FSInputFile(path=os.path.join(config.IMAGE_PATH, history_item.image))
            photo = types.InputMediaPhoto(media=img, caption=msg, show_caption_above_media=False)
        except (ValidationError, TypeError):
            photo = await get_input_media_hero_image("history", msg)

        await callback.message.edit_media(
            media=photo,
            reply_markup=kb.adjust(2, 2, 1).as_markup())

    except CustomError as error:
        msg, photo = await get_error_answer_photo(error)
        await callback.message.answer_photo(
            photo=photo,
            caption=msg,
            reply_markup=await menu_kb()
        )
