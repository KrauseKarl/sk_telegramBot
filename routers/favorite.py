from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from peewee import IntegrityError
from pydantic import ValidationError

from database.exceptions import *
from database.orm import *
from keyboards import *
from request import request_item_detail
from utils import *

favorite = Router()


async def create_favorite_instance(callback: CallbackQuery, state: FSMContext):
    if callback.data.startswith("favorite_add"):
        item_id = str(callback.data).split("_")[2]
        img_qnt = str(callback.data).split("_")[-1]
        data = await state.get_data()
        data['user'] = callback.from_user.id
        kb = await kb_builder(
            size=(2,),
            data_list=[
                {"свернуть": "delete_{0}_{1}".format(item_id, img_qnt)},
                {"отслеживать цену": "price"}
            ]
        )
    else:  # callback.data.startswith("fav_pre_add"):
        item_id = str(callback.data).split("_")[-1]
        response = await request_item_detail(item_id)
        item_data = await deserialize_item_detail(response, callback.from_user.id)
        data = dict()
        data["product_id"] = item_id
        data["user"] = callback.from_user.id
        data["title"] = item_data["title"]
        data["price"] = item_data["price"]
        data["reviews"] = item_data["reviews"]
        data["star"] = item_data["star"]
        data["url"] = item_data["url"]
        data["image"] = item_data["image"]
        kb = await builder_kb(
            data=[{"👀 подробно": "{0}_{1}".format("item", item_id)}], size=(1,)
        )

    return data, kb


@favorite.callback_query(F.data.startswith("fav_delete_"))
async def delete_favorite(callback: CallbackQuery) -> None:
    item_id = str(callback.data).split("_")[-1]
    page = int(callback.data.split("_")[-2])
    await orm_delete_favorite(item_id)
    await callback.answer('✅️ товар удален из избранного', show_alert=True)
    data_list = await orm_get_favorite_list(callback.from_user.id)

    paginator = Paginator(data_list, page=int(page))
    one_item = paginator.get_page()[0]
    msg = await favorite_info(one_item)
    msg = msg + "{0} из {1}".format(page, paginator.pages)

    # todo make func kb_page_builder and remove to pagination.py
    kb = InlineKeyboardBuilder()
    if page != 1:
        callback_previous = "fav_page_previous_{0}".format(page - 1)
        kb.add(InlineKeyboardButton(text="◀ Пред.", callback_data=callback_previous))
    callback_next = "fav_page_next_{0}".format(page + 1)
    kb.add(InlineKeyboardButton(text='След. ▶', callback_data=callback_next))
    kb.add(InlineKeyboardButton(text='главное меню', callback_data="menu"))
    kb.add(InlineKeyboardButton(
        text='❌ удалить',
        callback_data="fav_delete_{1}_{0}".format(one_item.product_id, page - 1))
    )
    try:
        img = FSInputFile(path=os.path.join(config.IMAGE_PATH, one_item.image))
        photo = InputMediaPhoto(media=img, caption=msg, show_caption_above_media=False)
    except (ValidationError, TypeError):
        photo = await get_input_media_hero_image("favorite", msg)
    await callback.message.edit_media(
        media=photo,
        reply_markup=kb.adjust(2, 2, 1).as_markup())


@favorite.callback_query(F.data.startswith("favorite_add") | F.data.startswith("fav_pre_add"))
async def add_favorite(callback: CallbackQuery, state: FSMContext) -> None:
    try:
        data, kb = await create_favorite_instance(callback, state)
        # todo add logger
        item, created = await orm_get_or_create_favorite(data)
        # todo add logger
        await callback.answer('⭐️ добавлен в избранное', show_alert=True)
        await callback.message.edit_reply_markup(reply_markup=kb)
    except IntegrityError as error:
        await callback.answer("⚠️ уже добавлено в избранное", show_alert=True)


@favorite.callback_query(F.data.startswith("favorites") | F.data.startswith("fav_page"))
async def favorite_page(callback: CallbackQuery) -> None:
    print(callback.data)
    try:
        data_list = await orm_get_favorite_list(callback.from_user.id)
        if callback.data.startswith("fav_page"):
            # todo make func make_paginate_history_list
            page = int(callback.data.split("_")[-1])
            paginator = Paginator(data_list, page=int(page))
            one_item = paginator.get_page()[0]
            msg = await favorite_info(one_item)
            msg = msg + "{0} из {1}".format(page, paginator.pages)

            # todo make func kb_page_builder and remove to pagination.py
            kb = InlineKeyboardBuilder()
            if callback.data.startswith("fav_page_next"):
                callback_previous = "fav_page_previous_{0}".format(page - 1)
                kb.add(InlineKeyboardButton(text="◀ Пред.", callback_data=callback_previous))
                if page != paginator.pages:
                    callback_next = "fav_page_next_{0}".format(page + 1)
                    kb.add(InlineKeyboardButton(text='След. ▶', callback_data=callback_next))
                    # if paginator.pages > 10:
                    #     callback_next = "page_next_{0}".format(page + 10)
                    #     kb.add(InlineKeyboardButton(text='След. 10 ▶', callback_data=callback_next))
            elif callback.data.startswith("fav_page_previous"):
                if page != 1:
                    callback_previous = "fav_page_previous_{0}".format(page - 1)
                    kb.add(InlineKeyboardButton(text="◀ Пред.", callback_data=callback_previous))
                    # if page > 10:
                    #     callback_previous = "page_previous_{0}".format(page - 10)
                    #     kb.add(InlineKeyboardButton(text="◀ Пред. 10", callback_data=callback_previous))
                callback_next = "fav_page_next_{0}".format(page + 1)
                kb.add(InlineKeyboardButton(text='След. ▶', callback_data=callback_next))
            kb.add(InlineKeyboardButton(text='главное меню', callback_data="menu"))
            kb.add(InlineKeyboardButton(
                text='❌ удалить',
                callback_data="fav_delete_{1}_{0}".format(one_item.product_id, page-1))
            )

            # todo make func kb_page_builder and remove to pagination.py
            img = one_item.image
            kb = kb.adjust(2, 2, 1).as_markup()
        else:
            msg, kb, img = await make_paginate_favorite_list(data_list)

        try:
            img = FSInputFile(path=os.path.join(config.IMAGE_PATH, img))
            photo = InputMediaPhoto(media=img, caption=msg, show_caption_above_media=False)
        except (ValidationError, TypeError):
            photo = await get_input_media_hero_image("favorite", msg)

        # todo make func make_paginate_list
        await callback.message.edit_media(
            media=photo,
            reply_markup=kb)

    except CustomError as error:
        msg, photo = await get_error_answer_photo(error)
        await callback.message.answer_photo(
            photo=photo,
            caption=msg,
            reply_markup=await menu_kb()
        )
