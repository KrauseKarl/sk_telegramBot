from aiogram import F, Router
from aiogram.filters import or_f
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton
from pydantic import ValidationError

from api_aliexpress.deserializers import *
from api_aliexpress.request import *
from api_telegram.callback_data import *
from api_telegram.crud.favorites import *
from api_telegram.statments import ItemFSM
from database.exceptions import *
from database.orm import *
from utils.media import *
from utils.message_info import *

favorite = Router()


@favorite.callback_query(FavoriteDeleteCBD.filter(F.action == FavAction.delete))
async def delete_favorite(call: CallbackQuery, data: FavoriteDeleteCBD) -> None:
    """

    :param call:
    :param data:
    :return:
    """
    await call.answer()
    item_id = data.item_id
    page = int(data.page)
    print(f'FAVORITE DELETE ENDPOINT\n{item_id= }\n{page}')
    await delete_favorite_instance(item_id)
    await call.answer('✅️ товар удален из избранного', show_alert=True)

    # data_list = await orm_get_favorite_list(call.from_user.id)
    # paginator = Paginator(data_list, page=int(page))

    # todo make func kb_page_builder and remove to pagination.py
    kb = InlineKeyboardBuilder()
    if page == 0:
        page += 1
        data_list = await orm_get_favorite_list(call.from_user.id)
        paginator = Paginator(data_list, page=int(page))
        if len(paginator.get_page()) == 0:
            msg = "у вас пока нет избранных товаров"
            photo = await get_input_media_hero_image("favorite", msg)
            kb.add(InlineKeyboardButton(text='🏠 назад', callback_data="menu"))
            await call.message.edit_media(
                media=photo,
                reply_markup=kb.adjust(2, 2, 1).as_markup()
            )
        item = paginator.get_page()[0]
        callback_next = "fav_page_next_{0}".format(page)
        kb.add(InlineKeyboardButton(text='След. ▶', callback_data=callback_next))
    elif page == 1:
        data_list = await orm_get_favorite_list(call.from_user.id)
        paginator = Paginator(data_list, page=int(page))
        item = paginator.get_page()[0]
        callback_next = "fav_page_next_{0}".format(page)
        kb.add(InlineKeyboardButton(text='След. ▶', callback_data=callback_next))
    else:
        data_list = await orm_get_favorite_list(call.from_user.id)
        paginator = Paginator(data_list, page=int(page))
        if paginator.pages > 1:
            callback_previous = "fav_page_previous_{0}".format(page - 1)
            kb.add(InlineKeyboardButton(text="◀ Пред.", callback_data=callback_previous))
            callback_next = "fav_page_next_{0}".format(page + 1)
            kb.add(InlineKeyboardButton(text='След. ▶', callback_data=callback_next))
        item = paginator.get_page()[0]
    # todo make func kb_page_builder and remove to pagination.py

    msg = await favorite_info(item)
    msg = msg + "{0} из {1}".format(page, paginator.pages)
    kb.add(
        InlineKeyboardButton(
            text='❌ удалить',
            callback_data=FavoriteDeleteCBD(
                action=FavAction.delete,
                item_id=item.product_id, page=str(page - 1)
            ).pack()
        )
    )
    kb.add(InlineKeyboardButton(text='🏠 меню', callback_data="menu"))

    try:
        img = types.FSInputFile(
            path=os.path.join(config.IMAGE_PATH, item.image)
        )
        photo = types.InputMediaPhoto(
            media=img, caption=msg, show_caption_above_media=False
        )
    except (ValidationError, TypeError):
        photo = await get_input_media_hero_image("favorite", msg)
    await call.message.edit_media(
        media=photo,
        reply_markup=kb.adjust(2, 2, 1).as_markup())


@favorite.callback_query(or_f(
    FavoriteAddCBD.filter(F.action == FavAction.list),
    FavoriteAddCBD.filter(F.action == FavAction.detail),
))
async def add_favorite(callback: CallbackQuery, callback_data: FavoriteAddCBD) -> None:
    """

    :param callback_data:
    :param callback:
    :return:
    """
    print('🟪 FAVORITE ADD ENDPOINT\n🟪 data = {call.data}')
    try:

        data, kb = await create_favorite_instance(callback, callback_data)
        # todo add logger

        # todo add logger
        msg = '{0:.50}\n\n✅\tдобавлено в избранное'.format(data.get("title"))
        await callback.answer(text=msg, show_alert=True)
        await callback.message.edit_reply_markup(reply_markup=kb)

    except FreeAPIExceededError as error:
        await callback.answer(show_alert=True, text="⚠️ ОШИБКА\n\n{0}".format(error))

    except IntegrityError as error:
        # todo add logger and record `error`
        await callback.answer(str(error), show_alert=True)


# F.data.startswith("favorites") | F.data.startswith("fav_page")
@favorite.callback_query(FavoritePageCBD.filter(F.action == FavAction.page))
async def get_favorite_list(call: CallbackQuery, callback_data: FavoritePageCBD) -> None:
    """

    :param callback_data:
    :param call:
    :return:
    """
    print('___1 🟪🟪🟪 FAVORITE ENDPOINT')

    try:
        data_list = await orm_get_favorite_list(call.from_user.id)
        print(f"___2 🟪{len(data_list) = }")
        print(f"___2 🟪{callback_data= }")
        if len(data_list) == 1:
            msg, kb, img = await make_paginate_favorite_list(data_list)
        else:
            if callback_data.page == FavPagination.first:
                msg, kb, img = await make_paginate_favorite_list(data_list)
            else:
                # if callback.data.startswith("fav_page"):
                # todo make func make_paginate_history_list
                # page = int(callback.data.split("_")[-1])
                page = callback_data.pages
                print(f"___3 🟪 {page= }")

                paginator = Paginator(data_list, page=int(page))
                item = paginator.get_page()[0]
                msg = await favorite_info(item)
                msg = msg + "{0} из {1}".format(page, paginator.pages)

                # todo make func kb_page_builder and remove to pagination.py
                kb = InlineKeyboardBuilder()
                if callback_data.page == FavPagination.next:
                    kb.add(InlineKeyboardButton(
                        text="◀ Пред.",
                        callback_data=FavoritePageCBD(
                            action=FavAction.page,
                            page=FavPagination.prev,
                            pages=page - 1
                        ).pack()))
                    if int(callback_data.page) < int(paginator.pages):
                        kb.add(InlineKeyboardButton(
                            text='След. ▶',
                            callback_data=FavoritePageCBD(
                                action=FavAction.page,
                                page=FavPagination.next,
                                pages=page + 1
                            ).pack()))
                elif callback_data.page == FavPagination.prev:
                    if int(callback_data.page) > 1:
                        kb.add(InlineKeyboardButton(text="◀ Пред.", callback_data=FavoritePageCBD(
                            action=FavAction.page,
                            page=FavPagination.prev,
                            pages=page - 1
                        ).pack()))
                    kb.add(InlineKeyboardButton(
                        text='След. ▶',
                        callback_data=FavoritePageCBD(
                            action=FavAction.page,
                            page=FavPagination.prev,
                            pages=page + 1
                        ).pack()
                    )
                    )
                kb.add(InlineKeyboardButton(text='🌐 web', callback_data="web"))
                kb.add(InlineKeyboardButton(text='🏠 меню', callback_data="menu"))
                kb.add(InlineKeyboardButton(
                    text='❌ удалить',
                    callback_data=FavoriteDeleteCBD(
                        action=FavAction.delete,
                        item_id=item.product_id,
                        page=str(page - 1)
                    ).pack()))
                kb = kb.adjust(2, 3).as_markup()
                # todo make func kb_page_builder and remove to pagination.py

                img = item.image
        try:
            # img = types.FSInputFile(
            #     path=os.path.join(config.IMAGE_PATH, img)
            # )
            photo = types.InputMediaPhoto(
                media=img, caption=msg, show_caption_above_media=False
            )
        except (ValidationError, TypeError):
            photo = await get_input_media_hero_image("favorite", msg)

        # todo make func make_paginate_list
        await call.message.edit_media(
            media=photo,
            reply_markup=kb)
    except TelegramBadRequest as error:
        await call.answer(f"⚠️ {str(error)}")
    except CustomError as error:
        msg, photo = await get_error_answer_photo(error)
        await call.message.answer_photo(
            photo=photo,
            caption=msg,
            reply_markup=await menu_kb()
        )
