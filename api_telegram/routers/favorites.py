import os

from aiogram import F, Router
from aiogram.filters import and_f
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from pydantic import ValidationError

from api_aliexpress.deserializers import *
from api_aliexpress.request import *
from api_telegram.callback_data import *
from api_telegram.statments import ItemFSM
from database.exceptions import *
from database.orm import *
from utils.media import *
from utils.message_info import *

favorite = Router()


async def create_favorite_instance(
        callback: types.CallbackQuery,
        state: FSMContext,
        callback_data: FavoriteAddCBD
):
    """

    :param callback:
    :param state:
    :return:
    """
    # if callback.data.startswith("favorite_add"):
    #     item_id = str(callback.data).split("_")[2]
    #     img_qnt = str(callback.data).split("_")[-1]
    #     data = await state.get_data()
    #     data['user'] = callback.from_user.id
    #     kb = await kb_builder(
    #         size=(2,),
    #         data_list=[
    #             {"свернуть": "delete_{0}_{1}".format(item_id, img_qnt)},
    #             {"отслеживать цену": "price"}
    #         ]
    #     )
    # else:  # callback.data.startswith("fav_pre_add"):
    # item_id = str(callback.data).split("_")[-1]
    item_id = callback_data.item_id
    response = await request_api(url=config.URL_API_ITEM_DETAIL, item_id=item_id)
    item_data = await deserialize_item_detail(response, callback.from_user.id)
    item_data["product_id"] = item_id
    key = callback_data.key
    api_page = callback_data.api_page
    _prev = callback_data.prev
    _next = callback_data.next
    _first = callback_data.first
    _last = callback_data.last

    prev_kb = ItemCBD(key=key, api_page=api_page, paginate_page=_prev).pack()
    next_kb = ItemCBD(key=key, api_page=api_page, paginate_page=_next).pack()
    first_kb = ItemCBD(key=key, api_page=api_page, paginate_page=_first).pack()
    last_kb = ItemCBD(key=key, api_page=api_page, paginate_page=_last).pack()
    detail = DetailCBD(item_id=item_id).pack()

    kb = await builder_kb(
        data=[
            {"⬅️ Пред.": prev_kb},
            {"След. ➡️": next_kb},
            {"⏪ Первая": first_kb},
            {"После. ⏩": last_kb},
            {"ℹ️ подробно": detail},
            {"🌐": "menu"},
            {"🏠 menu": "menu"}

        ],
        size=(2, 2, 2)
    )

    return item_data, kb


@favorite.callback_query(FavoriteDeleteCBD.filter(F.action == FavAction.delete))
async def delete_favorite(callback: types.CallbackQuery, callback_data: FavoriteDeleteCBD) -> None:
    """

    :param callback_data:
    :param callback:
    :return:
    """
    await callback.answer()
    item_id = callback_data.item_id
    page = int(callback_data.page)

    print(f'FAVORITE DELETE ENDPOINT\n{item_id= }\n{page}')

    # todo make delete func
    favorite_obj = await orm_get_favorite(item_id)
    try:
        img_path = os.path.join(config.IMAGE_PATH, favorite_obj.image)
        if os.path.isfile(img_path):
            os.remove(img_path)
    except TypeError:
        pass
    await orm_delete_favorite(item_id)
    # todo make delete func

    await callback.answer('✅️ товар удален из избранного', show_alert=True)
    data_list = await orm_get_favorite_list(callback.from_user.id)

    # paginator = Paginator(data_list, page=int(page))

    # todo make func kb_page_builder and remove to pagination.py
    kb = InlineKeyboardBuilder()
    if page == 0:
        page += 1
        print("page 0", page)
        data_list = await orm_get_favorite_list(callback.from_user.id)
        paginator = Paginator(data_list, page=int(page))
        print(f"page 0 paginator.get_page {paginator.get_page()= }")

        if len(paginator.get_page()) == 0:
            msg = "у вас пока нет избранных товаров"
            photo = await get_input_media_hero_image("favorite", msg)
            kb.add(InlineKeyboardButton(text='🏠 назад', callback_data="menu"))
            await callback.message.edit_media(
                media=photo,
                reply_markup=kb.adjust(2, 2, 1).as_markup()
            )
        one_item = paginator.get_page()[0]
        callback_next = "fav_page_next_{0}".format(page)
        kb.add(InlineKeyboardButton(text='След. ▶', callback_data=callback_next))

    elif page == 1:
        print("page 1")
        data_list = await orm_get_favorite_list(callback.from_user.id)
        paginator = Paginator(data_list, page=int(page))
        one_item = paginator.get_page()[0]
        print(f"page 1 paginator.get_page {paginator.get_page()= }")
        callback_next = "fav_page_next_{0}".format(page)
        kb.add(InlineKeyboardButton(text='След. ▶', callback_data=callback_next))
    else:
        print("page {}".format(page))
        data_list = await orm_get_favorite_list(callback.from_user.id)
        paginator = Paginator(data_list, page=int(page))
        if paginator.pages > 1:
            callback_previous = "fav_page_previous_{0}".format(page - 1)
            kb.add(InlineKeyboardButton(text="◀ Пред.", callback_data=callback_previous))
            callback_next = "fav_page_next_{0}".format(page + 1)
            kb.add(InlineKeyboardButton(text='След. ▶', callback_data=callback_next))
        one_item = paginator.get_page()[0]
        print(f"page  paginator.get_page {paginator.get_page()= }")
    msg = await favorite_info(one_item)
    msg = msg + "{0} из {1}".format(page, paginator.pages)
    kb.add(
        InlineKeyboardButton(
            text='❌ удалить',
            callback_data=FavoriteDeleteCBD(
                action=FavAction.delete,
                item_id=one_item.product_id, page=str(page - 1)
            ).pack()
        )
    )
    kb.add(InlineKeyboardButton(text='🏠 меню', callback_data="menu"))

    try:
        img = types.FSInputFile(
            path=os.path.join(config.IMAGE_PATH, one_item.image)
        )
        photo = types.InputMediaPhoto(
            media=img, caption=msg, show_caption_above_media=False
        )
    except (ValidationError, TypeError):
        photo = await get_input_media_hero_image("favorite", msg)
    await callback.message.edit_media(
        media=photo,
        reply_markup=kb.adjust(2, 2, 1).as_markup())


@favorite.callback_query(FavoriteAddCBD.filter(F.action == FavAction.list))
async def add_favorite(callback: types.CallbackQuery, state: FSMContext, callback_data: FavoriteAddCBD) -> None:
    """

    :param callback_data:
    :param callback:
    :param state:
    :return:
    """
    print('🟪 FAVORITE ADD ENDPOINT')
    print(f"🟪 data = {callback.data}")

    try:
        data, kb = await create_favorite_instance(callback, state, callback_data)
        # data = await create_favorite_instance(callback, state, callback_data)
        # todo add logger
        item, created = await orm_get_or_create_favorite(data)
        # todo add logger
        # await callback.answer('✅ добавлен в избранное', show_alert=True)
        await callback.message.edit_reply_markup(reply_markup=kb)
    except FreeAPIExceededError as error:
        await callback.answer(show_alert=True, text="⚠️ ОШИБКА\n\n{0}".format(error))
    except IntegrityError as error:
        await callback.answer("⚠️ уже добавлено в избранное", show_alert=True)


# F.data.startswith("favorites") | F.data.startswith("fav_page")
@favorite.callback_query(FavoritePageCBD.filter(F.action == FavAction.page))
async def get_favorite_list(
        callback: types.CallbackQuery,
        callback_data: FavoritePageCBD
) -> None:
    """

    :param callback_data:
    :param callback:
    :return:
    """
    print('___1 🟪🟪🟪 FAVORITE ENDPOINT')
    await callback.answer()
    try:
        data_list = await orm_get_favorite_list(callback.from_user.id)
        print(f"___2 🟪{len(data_list) = }")

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
                one_item = paginator.get_page()[0]
                msg = await favorite_info(one_item)
                msg = msg + "{0} из {1}".format(page, paginator.pages)

                # todo make func kb_page_builder and remove to pagination.py
                kb = InlineKeyboardBuilder()
                if callback_data.page == FavPagination.next:
                    callback_previous = FavoritePageCBD(
                        action=FavAction.page,
                        page=FavPagination.prev,
                        pages=page - 1
                    ).pack()
                    kb.add(InlineKeyboardButton(text="◀ Пред.", callback_data=callback_previous))
                    if page != paginator.pages:
                        callback_next = FavoritePageCBD(
                            action=FavAction.page,
                            page=FavPagination.next,
                            pages=page + 1
                        ).pack()
                        kb.add(InlineKeyboardButton(text='След. ▶', callback_data=callback_next))

                elif callback_data.page == FavPagination.prev:
                    if page != 1:
                        callback_previous = FavoritePageCBD(
                            action=FavAction.page,
                            page=FavPagination.prev,
                            pages=page - 1
                        ).pack()
                        kb.add(InlineKeyboardButton(text="◀ Пред.", callback_data=callback_previous))
                    callback_next = FavoritePageCBD(
                        action=FavAction.page,
                        page=FavPagination.prev,
                        pages=page + 1
                    ).pack()
                    kb.add(InlineKeyboardButton(text='След. ▶', callback_data=callback_next))
                delete_data = FavoriteDeleteCBD(
                    action=FavAction.delete,
                    item_id=one_item.product_id,
                    page=str(page - 1)
                ).pack()

                kb.add(InlineKeyboardButton(text='❌ удалить', callback_data=delete_data))
                kb.add(InlineKeyboardButton(text='🏠 меню', callback_data="menu"))
                # todo make func kb_page_builder and remove to pagination.py
                img = one_item.image
                kb = kb.adjust(2, 2, 2).as_markup()

        try:
            img = types.FSInputFile(
                path=os.path.join(config.IMAGE_PATH, img)
            )
            photo = types.InputMediaPhoto(
                media=img, caption=msg, show_caption_above_media=False
            )
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
