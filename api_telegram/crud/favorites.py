from aiogram.types import CallbackQuery

from api_aliexpress.deserializers import *
from api_aliexpress.request import *
from api_telegram.callback_data import *
from api_telegram.keyboards import *
from core import config


async def create_favorite_instance(call: CallbackQuery, data: FavoriteAddCBD):
    """

    :param data:
    :param call:
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

    item_id = data.item_id
    response = await request_api(url=config.URL_API_ITEM_DETAIL, item_id=item_id)
    item_data = await deserialize_item_detail(response, call.from_user.id)
    item_data["product_id"] = item_id

    prev_kb = ItemCBD(key=data.key, api_page=data.api_page, paginate_page=data.prev).pack()
    next_kb = ItemCBD(key=data.key, api_page=data.api_page, paginate_page=data.next).pack()
    first_kb = ItemCBD(key=data.key, api_page=data.api_page, paginate_page=data.first).pack()
    last_kb = ItemCBD(key=data.key, api_page=data.api_page, paginate_page=data.last).pack()
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
        size=(2, 2, 3)
    )

    return item_data, kb


async def delete_favorite_instance(item_id: str) -> bool:
    favorite_obj = await orm_get_favorite(item_id)
    await delete_img_from_static(favorite_obj)
    await orm_delete_favorite(item_id)
    return True


