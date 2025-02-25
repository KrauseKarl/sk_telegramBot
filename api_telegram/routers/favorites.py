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


@favorite.callback_query(FavoritePageCBD.filter(F.action == FavAction.page))
async def get_favorite_list(call: CallbackQuery, callback_data: FavoritePageCBD) -> None:
    """

    :param callback_data:
    :param call:
    :return:
    """
    print('🟪 FAVORITE ENDPOINT')
    try:
        data_list = await orm_get_favorite_list(call.from_user.id)
        msg = "⭕️ у вас пока нет избранных товаров"
        img = None
        keyboard_list = []
        if len(data_list) > 0:
            paginator = Paginator(data_list, page=callback_data.page)
            item = paginator.get_page()[0]
            img = item.image
            msg = await favorite_info(item)
            keyboard_list.extend(
                await get_paginate_favorite_kb(
                    page=int(callback_data.page),
                    paginator=paginator,
                    item_id=item.product_id,
                    navigate=callback_data.navigate,
                    len_data=len(data_list)
                )
            )
            msg = msg + "\n{0} из {1}".format(callback_data.page, paginator.pages)
        keyboard_list.append({"🏠 menu": "menu"})

        kb = await kb_builder(data_list=keyboard_list, size=(2,))
        try:
            # img = types.FSInputFile(path=os.path.join(config.IMAGE_PATH, img))
            photo = types.InputMediaPhoto(media=img, caption=msg)
        except (ValidationError, TypeError):
            photo = await get_input_media_hero_image("favorite", msg)
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
        msg = '{0:.50}\n\n✅\tдобавлено в избранное'.format(data.get("title"))
        await callback.answer(text=msg, show_alert=True)
        await callback.message.edit_reply_markup(reply_markup=kb)

    except FreeAPIExceededError as error:
        await callback.answer(show_alert=True, text="⚠️ ОШИБКА\n\n{0}".format(error))

    except IntegrityError as error:
        # todo add logger and record `error`
        await callback.answer(str(error), show_alert=True)


@favorite.callback_query(FavoriteDeleteCBD.filter(F.action == FavAction.delete))
async def delete_favorite(call: CallbackQuery, callback_data: FavoriteDeleteCBD) -> None:
    """

    :param call:
    :param callback_data:
    :return:
    """
    msg = "у вас пока нет избранных товаров"
    keyboard_list = []
    img = None
    print(f'___FAVORITE DELETE ENDPOINT\n___item_id ={callback_data.item_id}\n___page = {callback_data.page}')
    data_list = await orm_get_favorite_list(call.from_user.id)
    print('____LEN DATA LIST', len(data_list))
    page = int(callback_data.page)
    current_page = 1
    #       [1] -> [x] -> NONE
    #       1st page 1 item_list > msg = "у вас пока нет избранных товаров"           add kb=["^"] no items

    #       [__1__][2] -> [x][__2->1__]-> [__1__]                                     kb = None
    #       1st page 2 item_list > (go to next)   after_del_page  = page + 1          kb=["^", "X"]

    #       [__1__][2][3][4][5] -> [x][__2->1__][3->2 4->3 5->4] -> [__1__][2][3][4]   add kb = [">"]
    #       1st page 5 item_list > (go to next)   after_del_page  = page + 1          kb=["^", "X",  ">"]

    #       [1][__2__] -> [1][x] -> [__1__]                                            kb = None
    #       -1st page 2 item_list > (back to prev) after_del_page  = page - 1          kb=["^", "X"]

    #       [1][2][3][4][__5__] -> [1][2][3][4][x] -> [1][2][3][__4__]                 kb=["<"]
    #       -1st page 5 item_list > (back to prev) after_del_page  = page - 1          kb=["^", "X", "<"]

    # [1][2][__3__][4][5] -> [1][2][x][4->3][5->4] -> [1][__2__][3][4]           kb=["<", ">"]
    #  3rd page 5 item_list > (back to prev) after_del_page  = page - 1          kb=["^", "X", "<", ">"]

    if len(data_list) == 1:
        if page == len(data_list):
            pass
            # msg = "у вас пока нет избранных товаров"
    else:
        if len(data_list) == 2:
            if page == 1:
                page = page + 1
                current_page = 1
                next_button = FavoritePageCBD(action=FavAction.page, navigate=FavPagination.next, page=str(page)).pack()
                keyboard_list.append({"След. ➡️": next_button})
            elif page == len(data_list):
                page = page - 1
                current_page = page
                prev_button = FavoritePageCBD(action=FavAction.page, navigate=FavPagination.prev, page=str(page)).pack()
                keyboard_list.append({"⬅️ Пред.": prev_button})
        elif len(data_list) > 2:
            if page == 1:
                page = page + 1
                current_page = 1
                next_button = FavoritePageCBD(action=FavAction.page, navigate=FavPagination.next, page=str(page)).pack()
                keyboard_list.append({"След. ➡️": next_button})
            elif 1 < page < len(data_list):
                page = page - 1
                current_page = page
                prev_button = FavoritePageCBD(action=FavAction.page, navigate=FavPagination.prev, page=str(page)).pack()
                keyboard_list.append({"⬅️ Пред.": prev_button})
                next_button = FavoritePageCBD(action=FavAction.page, navigate=FavPagination.next, page=str(page)).pack()
                keyboard_list.append({"След. ➡️": next_button})
            elif page == len(data_list):
                page = page - 1
                current_page = page
                prev_button = FavoritePageCBD(action=FavAction.page, navigate=FavPagination.prev, page=str(page)).pack()
                keyboard_list.append({"⬅️ Пред.": prev_button})

        delete_button = FavoriteDeleteCBD(action=FavAction.delete, item_id=callback_data.item_id, page=str(page)).pack()
        keyboard_list.append({"❌ удалить": delete_button})

        await delete_favorite_instance(callback_data.item_id)

        data_list = await orm_get_favorite_list(call.from_user.id)
        paginator = Paginator(data_list, page=int(page))

        try:
            item = paginator.get_page()[0]
            img = item.image
            msg = await favorite_info(item)
            msg = msg + "{0} из {1}".format(current_page, paginator.pages)
            # keyboard_list = await get_paginate_favorite_delete(
            #     page=int(callback_data.page),
            #     paginator=paginator,
            #     item_id=callback_data.item_id
            # )
        except IndexError:
            img = None
    keyboard_list.append({"🏠 menu": "menu"})
    kb = await kb_builder(data_list=keyboard_list, size=(2, 2))



    try:
        # img = types.FSInputFile(path=os.path.join(config.IMAGE_PATH, item.image))
        photo = types.InputMediaPhoto(media=img, caption=msg)
    except (ValidationError, TypeError):
        photo = await get_input_media_hero_image("favorite", msg)
    await call.answer('✅️ товар удален из избранного', show_alert=True)
    await call.message.edit_media(
        media=photo,
        reply_markup=kb)
