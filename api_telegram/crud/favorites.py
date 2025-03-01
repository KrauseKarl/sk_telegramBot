from aiogram.types import CallbackQuery
from pydantic import ValidationError

from api_aliexpress.deserializers import *
from api_aliexpress.request import *
from api_telegram.callback_data import *
from api_telegram.keyboards import *
from api_telegram.paginations import paginate_favorite_list_kb
from core import config
from utils.message_info import favorite_info


async def create_favorite_instance(call: CallbackQuery, data: FavoriteAddCBD):
    """

    :param data:
    :param call:
    :return:
    """

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
    kb = ItemPaginationBtn(
        key=data.key,
        api_page=data.api_page,
        paginator_len=int(data.last),
        item_id=data.item_id
    )
    if data.action == FavAction.detail:
        kb.add_buttons([
            kb.detail('back', data.page, DetailAction.view),
            kb.btn_text('price')
        ]).add_markups([1, 2, 3])
    if data.action == FavAction.list:
        kb.add_buttons([
            kb.btn_data('prev', data.prev),
            kb.btn_data('next', data.next),
            kb.btn_data('first', data.first),
            kb.btn_data('last', data.last),
            kb.detail('view', data.page, DetailAction.view),
            kb.btn_text('menu'),
            kb.btn_text('web'),
        ]).add_markups([2, 2, 3])

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


async def get_favorite_list(query, data):
    data_list = await orm_get_favorite_list(query.from_user.id)

    if len(data_list) > 0:
        paginator = Paginator(data_list, page=data.page)
        item = paginator.get_page()[0]
        img = item.image
        msg = await favorite_info(item, data.page, paginator.pages)
        kb = await paginate_favorite_list_kb(
            page=int(data.page),
            item_id=item.product_id,
            navigate=data.navigate,
            len_data=paginator.len
        )
    else:
        msg = "⭕️ у вас пока нет избранных товаров"
        img = None
        kb = BasePaginationBtn()
        kb.add_button(kb.btn_text('menu'))
    try:
        # img = types.FSInputFile(path=os.path.join(config.IMAGE_PATH, img))
        photo = types.InputMediaPhoto(media=img, caption=msg)
    except (ValidationError, TypeError):
        photo = await get_input_media_hero_image("favorite", msg)
    return msg, photo, kb

# async def make_paginate_favorite_list(
#         favorite_list: List[Favorite], page: int = 1
# ):
#     kb = FavoritePaginationBtn()
#     if len(favorite_list) == 0:
#         msg = "⭕️ у вас пока нет избранных товаров"
#         kb = await kb_builder(data_list=[{"🏠 меню": "menu"}], size=(1,))
#         return msg, kb, None
#     else:
#         paginator = Paginator(favorite_list, page=page)
#         item = paginator.get_page()[0]
#         msg = await favorite_info(item)
#         msg = msg + "\n{0} из {1}".format(page, paginator.pages)
#         if len(favorite_list) == 1:
#             kb = await kb_builder(
#                 size=(1,),
#                 data_list=[
#                     {"🏠 меню": "menu"}
#                 ]
#             )
#         else:
#
#             next_page = FavoritePageCBD(
#                 action=FavAction.page,
#                 page=FavPagination.next,
#                 pages=int(page) + 1
#             ).pack()
#             delete = FavoriteDeleteCBD(
#                 action=FavAction.delete,
#                 item_id=item.product_id,
#                 page=str(page - 1)
#             ).pack()
#
#             kb = await kb_builder(
#                 size=(1, 2),
#                 data_list=[
#                     {"След. ▶": next_page},
#                     {"❌ удалить": delete},
#                     {"🏠 меню": "menu"},
#                 ]
#             )
#         return msg, kb, item.image
