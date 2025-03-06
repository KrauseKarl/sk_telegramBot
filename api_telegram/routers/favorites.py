from aiogram import F, Router
from aiogram.filters import or_f
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton
from pydantic import ValidationError

from api_aliexpress.deserializers import *
from api_aliexpress.request import *
from api_telegram.callback_data import *
from api_telegram.crud.favorites import *
from api_telegram.paginations import paginate_favorite_list_kb
from api_telegram.statments import ItemFSM
from database.exceptions import *
from database.orm import *
from utils.media import *
from utils.message_info import *

favorite = Router()


@favorite.callback_query(FavoritePageCBD.filter(F.action == FavAction.page))
async def request_favorite_list(callback: CallbackQuery, callback_data: FavoritePageCBD) -> None:
    """

    :param callback:
    :param callback_data:
    :return:
    """
    print('🟪 FAVORITE ENDPOINT')
    try:
        msg, photo, kb = await get_favorite_list(callback, callback_data)
        await callback.message.edit_media(
            media=photo,
            reply_markup=kb.create_kb())

    except TelegramBadRequest as error:
        await callback.answer(f"⚠️ {str(error)}")
    except CustomError as error:
        msg, photo = await get_error_answer_photo(error)
        await callback.message.answer_photo(
            photo=photo,
            caption=msg,
            reply_markup=await menu_kb()
        )


@favorite.callback_query(FavoriteAddCBD.filter(F.action.in_({FavAction.list, FavAction.detail})))
async def add_favorite(callback: CallbackQuery, callback_data: FavoriteAddCBD) -> None:
    """

    :param callback_data:
    :param callback:
    :return:
    """
    print('🟪 FAVORITE ADD ENDPOINT\n🟪 data = {call.data}')
    try:
        page = callback_data.page
        total_pages = callback_data.last
        api_page = callback_data.api_page
        item_id = callback_data.item_id

        data, kb = await create_favorite_instance(callback, callback_data)
        card = await refresh_tg_answer(data, item_id, page, total_pages, api_page)
        # todo add logger

        msg = '{0:.50}\n\n✅\tдобавлено в избранное'.format(data.get("title"))
        await callback.answer(text=msg, show_alert=True)

        # await callback.message.edit_reply_markup(reply_markup=kb)
        await callback.message.edit_media(media=card, reply_markup=kb)

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

    msg = ""
    page = int(callback_data.page)
    current_page = 1

    await delete_favorite_instance(callback_data.item_id)
    print(f"PAGE {callback_data.page}")
    print(f"ACT  {callback_data.action}")
    print(f"ID   {callback_data.item_id}")
    data_list = await orm_get_favorite_list(call.from_user.id)
    paginator = Paginator(data_list, page=int(page))
    kb = KeyBoardFactory()
    btn = FavoritePaginationBtn_(item_id=callback_data.item_id)
    print(f"❌len  {paginator.len}")
    print(f"❌page  {page}")
    print(f"❌page  page > paginator.len =  {page > paginator.len}")
    ########################################################################################################
    if paginator.len == 1:
        # keyboard_list.append({"⬅️": await prev_btn(page)})
        msg = "❤️1 page = 1 items"
    else:
        if paginator.len == 2:
            if page == 1:
                page = 1
                current_page = page
                kb.add_button({"➡️": btn.next_bt(page)})
                msg = '🧡first page 2 items'
            elif page == paginator.len:
                page -= 1
                current_page = 1
                kb.add_button({"⬅️": btn.prev_bt(page)})
                msg = '💛last page 2 items'
            elif page > paginator.len:
                page = paginator.len
                current_page = page
                kb.add_button({"⬅️": btn.prev_bt(page - 1)})
                msg = '🤎 last page 2 items'

        elif paginator.len > 2:
            if page == 1:
                page += 1
                current_page = 1
                kb.add_button({"➡️": btn.next_bt(page)})
                msg = '💚first page many items'
            elif 1 < page < paginator.len:
                page -= 1
                current_page = page
                # keyboard_list.append({"⬅️": await prev_btn(page)})
                # keyboard_list.append({"➡️": await next_btn(page)})
                buttons = [{"⬅️": btn.prev_bt(page)}, {"➡️": btn.next_bt(page)}]
                kb.add_buttons(buttons)

                msg = '💙middle page many items'
            elif page == paginator.len:
                page -= 1
                current_page = page
                # keyboard_list.append({"⬅️": await prev_btn(page)})
                kb.add_button({"⬅️": btn.prev_bt(page)})
                msg = '🤍 last page many items == '
            elif page > paginator.len:
                page -= 1
                current_page = page
                # keyboard_list.append({"⬅️": await prev_btn(page)})
                kb.add_button({"⬅️": btn.prev_bt(page - 1)})
                msg = '💜 last page many items'
        ########################################################################################################
    # print(f'✅️ {msg = } page [{page=}]  current [{current_page}] prev [{prev_button}] next [{next_button}]')
    ########################################################################################################
    try:
        paginator = Paginator(data_list, page=int(current_page))
        item_id = paginator.get_page()[0].product_id
        kb.add_button({"❌ удалить": btn.delete_btn(current_page, item_id)})
    except:
        pass
    ########################################################################################################
    try:
        item = paginator.get_page()[0]
        msg = await favorite_info(item, page, paginator.len)
        img = item.image if item.image else None
    except IndexError:
        img = None
    kb.add_button({"🏠 меню": "menu"}).add_markups([2, 2])

    try:
        # img = types.FSInputFile(path=os.path.join(config.IMAGE_PATH, item.image))
        photo = types.InputMediaPhoto(media=img, caption=msg)
    except (ValidationError, TypeError):
        photo = await get_input_media_hero_image("favorite", msg)

    await call.answer('✅️ товар удален из избранного', show_alert=True)

    await call.message.edit_media(media=photo, reply_markup=kb.create_kb())
