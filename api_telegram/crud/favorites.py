from aiogram.types import CallbackQuery

from api_aliexpress.deserializers import *
from api_aliexpress.request import *
from api_telegram.callback_data import *
from api_telegram.keyboards import *
from core import config
from utils.message_info import favorite_info


async def create_favorite_instance(call: CallbackQuery, data: FavoriteAddCBD):
    """

    :param data:
    :param call:
    :return:
    """

    kb = PaginationKB()
    item = await orm_get_favorite(data.item_id)
    print(f'🌳🌳🌳 favorite exist = {item}')
    if item:
        raise IntegrityError("⚠️ уже добавлено в избранное")
    #####################################################
    if config.FAKE_MODE:
        response = await request_api_fake_favorite(data.item_id)
        item_data = await deserialize_item_detail_fake(response, call.from_user.id)
    else:
        response = await request_api(
            url=config.URL_API_ITEM_DETAIL,
            item_id=data.item_id
        )
        item_data = await deserialize_item_detail(response, call.from_user.id)
    ##########################################################
    item_data["product_id"] = data.item_id
    await orm_get_or_create_favorite(item_data)

    if data.action == FavAction.detail:
        detail_btn = DetailPaginationBtn(data=data).detail()
        buttons = [{"🔙 назад": detail_btn}, {"📉 отслеживать цену": "price"}]
        kb.add_buttons(buttons).add_markups([1, 2, 3])
    if data.action == FavAction.list:
        btn = ItemPaginationBtn(
            key=data.key,
            api_page=data.api_page,
            paginator_len=int(data.last)
        )
        buttons = [
            {"⬅️ Пред.": btn.btn(data.prev)},
            {"След. ➡️": btn.btn(data.next)},
            {"⏪ Первая": btn.btn(data.first)},
            {"После. ⏩": btn.btn(data.last)},
            {"ℹ️ подробно": btn.detail(data.page, data.item_id)},
            {"🌐": "menu"},
            {"🏠 menu": "menu"}
        ]
        kb.add_buttons(buttons).add_markups([2, 2, 3])

    return item_data, kb.create_kb()


async def delete_favorite_instance(item_id: str) -> bool:
    favorite_obj = await orm_get_favorite(item_id)
    # await delete_img_from_static(favorite_obj)
    try:
        await orm_delete_favorite(item_id)
        return True
    except Exception as error:
        print("delete error = ", error)
        return False


async def make_paginate_favorite_list(
        favorite_list: List[Favorite], page: int = 1
):
    if len(favorite_list) == 0:
        msg = "⭕️ у вас пока нет избранных товаров"
        kb = await kb_builder(data_list=[{"🏠 меню": "menu"}], size=(1,))
        return msg, kb, None
    else:
        paginator = Paginator(favorite_list, page=page)
        item = paginator.get_page()[0]
        msg = await favorite_info(item)
        msg = msg + "\n{0} из {1}".format(page, paginator.pages)
        if len(favorite_list) == 1:
            kb = await kb_builder(
                size=(1,),
                data_list=[
                    {"🏠 меню": "menu"}
                ]
            )
        else:

            next_page = FavoritePageCBD(
                action=FavAction.page,
                page=FavPagination.next,
                pages=int(page) + 1
            ).pack()
            delete = FavoriteDeleteCBD(
                action=FavAction.delete,
                item_id=item.product_id,
                page=str(page - 1)
            ).pack()

            kb = await kb_builder(
                size=(1, 2),
                data_list=[
                    {"След. ▶": next_page},
                    {"❌ удалить": delete},
                    {"🏠 меню": "menu"},
                ]
            )
        return msg, kb, item.image
