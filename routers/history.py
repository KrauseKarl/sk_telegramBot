from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from pydantic import ValidationError

from database.exceptions import CustomError
from database.orm import *
from utils import *

history = Router()


# HISTORY #############################################################################################################
@history.callback_query(F.data.startswith("history"))
async def history_callback(callback: CallbackQuery) -> None:
    try:
        history_list = await orm_get_history_list(callback.from_user.id)
        msg, kb = await make_paginate_history_list(history_list)
        await callback.message.edit_media(
            media=await get_input_media_hero_image('history', msg),
            reply_markup=kb
        )
    except CustomError as error:
        await callback.message.edit_media(
            media=await get_error_answer_media(error),
            reply_markup=menu_kb
        )


@history.message(Command("history"))
async def history_message(message: Message) -> None:
    try:
        history_list = await orm_get_history_list(message.from_user.id)
        msg, kb = await make_paginate_history_list(history_list)
        await message.answer_photo(
            photo=await get_fs_input_hero_image("history"),
            caption=msg,
            reply_markup=kb
        )
    except CustomError as error:
        msg, photo = await get_error_answer_photo(error)
        await message.answer_photo(
            photo=photo,
            caption=msg,
            reply_markup=menu_kb
        )


@history.callback_query(F.data.startswith("page"))
async def history_page(callback: Message | CallbackQuery) -> None:
    try:
        history_list = await orm_get_history_list(callback.from_user.id)

        # todo make func make_paginate_history_list
        page = int(callback.data.split("_")[2])
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
                #     kb.add(InlineKeyboardButton(text='След. 10 ▶', callback_data=callback_next))
        elif callback.data.startswith("page_previous"):
            if page != 1:
                callback_previous = "page_previous_{0}".format(page - 1)
                kb.add(InlineKeyboardButton(text="◀ Пред.", callback_data=callback_previous))
                # if page > 10:
                #     callback_previous = "page_previous_{0}".format(page - 10)
                #     kb.add(InlineKeyboardButton(text="◀ Пред. 10", callback_data=callback_previous))
            callback_next = "page_next_{0}".format(page + 1)
            kb.add(InlineKeyboardButton(text='След. ▶', callback_data=callback_next))
        kb.add(InlineKeyboardButton(text='главное меню', callback_data="menu"))
        # todo make func kb_page_builder and remove to pagination.py

        try:
            img = FSInputFile(path=os.path.join(config.IMAGE_PATH, history_item.image))
            photo = InputMediaPhoto(media=img, caption=msg, show_caption_above_media=False)
        except (ValidationError, TypeError):
            photo = await get_input_media_hero_image("history", msg)

        # todo make func make_paginate_history_list
        await callback.message.edit_media(
            media=photo,
            reply_markup=kb.adjust(2, 2, 1).as_markup())

    except CustomError as error:
        msg, photo = await get_error_answer_photo(error)
        await callback.message.answer_photo(
            photo=photo,
            caption=msg,
            reply_markup=menu_kb
        )