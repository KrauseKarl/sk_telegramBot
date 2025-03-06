from aiogram import types
from aiogram.filters.callback_data import CallbackData

from api_aliexpress.request import request_api
from api_redis.handlers import redis_get_data_from_cache
from api_telegram.callback_data import DetailAction, CacheKey, FavPagination, RevNavigate, ReviewCBD
from api_telegram.crud.items import refresh_params_dict, get_query_from_db
from api_telegram.keyboards import (
    ItemPaginationBtn,
    builder_kb,
    FavoritePaginationBtn_,
    KeyBoardFactory,
    FavoritePaginationBtn, RevPaginationBtn
)
from core import config
from database.orm import orm_get_favorite


async def get_web_link(item_id: str):
    return "https://www.aliexpress.com/item/{0}.html".format(item_id)


async def paginate_item_list_kb(params, callback_data_api_page):
    """

    :param params:
    :return:
    """
    key = params.get("key")
    api_page = int(params.get("api_page"))
    page = int(params.get("page"))
    item_id = params.get("item").get('itemId')
    len_data = params.get("total_pages")

    kb = ItemPaginationBtn(
        key=key,
        api_page=str(api_page),
        paginator_len=len_data,
        item_id=item_id
    )

    if api_page == 1 and int(page) == 1:
        kb.add_buttons(
            [kb.btn('next', int(page) + 1), kb.last_btn()]
        ).add_markups([1, 1])
    elif api_page > 1 and int(page) == 1:

        # todo refactor this part ######################################################################################
        # try to find previous item_list in cache
        prev_cache_key = CacheKey(key=key, api_page=str(api_page - 1), extra='list').pack()
        prev_list = await redis_get_data_from_cache(prev_cache_key)

        # if  previous item_list not exist in cache
        # make new request to API
        if prev_list is None:
            params = dict(url=config.URL_API_ITEM_LIST)
            params = await get_query_from_db(key, params)
            params['page'] = str(callback_data_api_page)
            prev_list = await request_api(params)

        # finally fins the last page in previous item_list
        prev_paginate_page = len(prev_list)
        # todo refactor this part ######################################################################################
        kb.add_buttons([
            kb.btn('prev', prev_paginate_page, api_page - 1),
            kb.btn('next', 2),
            kb.last_btn()
        ]).add_markups([2, 1])

    elif len_data > int(page) > 1:

        kb.add_buttons([
            kb.btn("prev", str(page - 1 if page - 1 > 1 else 1)),
            kb.btn("next", str(page + 1 if page + 1 < len_data else len_data + 1)),
            kb.first_btn(),
            kb.last_btn()
        ]).add_markups([2, 2])
    elif int(page) == len_data:
        # "последняя страница"
        kb.add_buttons([
            kb.btn("prev", str(page - 1 if page - 1 != 0 else 1)),
            kb.btn("next", str(page + 1)),
            kb.first_btn(),
        ]).add_markups([2, 1])

    data_web = ("url", await get_web_link(item_id))
    kb.add_buttons([
        kb.detail('detail', page, DetailAction.go_view),
        kb.btn_text("menu"),
        kb.btn_data("web", data_web),
    ]).add_markup(3)

    is_favorite = await orm_get_favorite(item_id)
    if is_favorite is None:
        kb.add_button(kb.favorite(page)).update_markup(4)
    return await builder_kb(kb.get_kb(), size=kb.get_markup())


async def paginate_favorite_list_kb(page: int, item_id, navigate: str, len_data: int):
    """

    :param page:
    :param item_id:
    :param navigate:
    :param len_data:
    :return:
    """
    kb = FavoritePaginationBtn(item_id)
    buttons = list()
    if len_data > 1:
        if navigate == FavPagination.first:
            buttons.append(kb.add_button(kb.pg(page).next_btn(1)))

        elif navigate == FavPagination.next:
            buttons.append(kb.add_button(kb.pg(page).prev_btn(-1)))
            if page < len_data:
                buttons.append(kb.add_button(kb.pg(page).next_btn(1)))

        elif navigate == FavPagination.prev:
            if page > 1:
                buttons.append(kb.add_button(kb.pg(page).prev_btn(-1)))
            buttons.append(kb.add_button(kb.pg(page).next_btn(1)))
        kb.add_markup(len(buttons))
        kb.add_buttons([kb.delete_btn(), kb.btn_text("menu")]).add_markup(2)

    return kb


async def pagination_review_kb(data_list: list, data: ReviewCBD):
    kb = RevPaginationBtn(
        key=data.key,
        api_page=data.api_page,
        item_id=data.item_id,
        paginator_len=data.paginator_len
    )
    if data_list is not None:
        if data.paginator_len > 1:
            if data.navigate == RevNavigate.first:
                kb.add_button(kb.next_btn(data.page, int(data.review_page) + 1)).add_markup(1)
            elif data.navigate == RevNavigate.next:
                kb.add_button(kb.prev_btn(data.page, int(data.review_page) - 1)).add_markup(2)
                if int(data.review_page) < data.paginator_len:
                    kb.add_button(kb.next_btn(data.page, int(data.review_page) + 1)).add_markup(2)
            elif data.navigate == RevNavigate.prev:
                if int(data.review_page) > 1:
                    kb.add_button(kb.prev_btn(data.page, int(data.review_page) - 1)).add_markup(2)
                kb.add_button(kb.next_btn(data.page, int(data.review_page) + 1)).add_markup(2)

    back_button = kb.detail("back", data.page, DetailAction.back_detail)
    kb.add_button(back_button).add_markups([1])
    return kb


async def paginate_review_list_kb(page: int, item_id, navigate: str, len_data: int):
    """

    :param page:
    :param item_id:
    :param navigate:
    :param len_data:
    :return:
    """
    kb = KeyBoardFactory()
    btn = FavoritePaginationBtn_(item_id)

    if len_data > 1:
        if navigate == FavPagination.first:
            kb.add_button({"След. ➡️": btn.next_bt(page)}).add_markup(1)

        elif navigate == FavPagination.next:
            kb.add_button({"⬅️ Пред.": btn.prev_bt(page)}).add_markup(1)
            if page < len_data:
                kb.add_button({"След. ➡️": btn.next_bt(page)}).update_markup(2)

        elif navigate == FavPagination.prev:
            kb.add_button({"След. ➡️": btn.next_bt(page)}).add_markup(1)
            if page > 1:
                kb.add_button({"⬅️ Пред.": btn.prev_bt(page)}).update_markup(2)

    buttons = [{"🏠 menu": "menu"}]
    kb.add_buttons(buttons).add_markup(1)

    return kb.create_kb()


async def paginate_favorite_delete_kb(
        page: int,
        len_data: int,
        item_id
):
    pass
    # keyboard_list = []
    # if page == 0:
    #     page += 1
    #     if len_data == 0:
    #         pass
    #     keyboard_list.append({"След. ➡️": await next_button(page)})
    # elif page == 1:
    #     keyboard_list.append({"След. ➡️": await next_button(page)})
    # else:
    #     if len_data > 1:
    #         keyboard_list.extend(
    #             [
    #                 {"⬅️ Пред.": await prev_button(page)},
    #                 {"След. ➡️": await next_button(page)}
    #             ]
    #         )
    # keyboard_list.append({"❌ удалить": await delete_button(page - 1, item_id)})
    # return keyboard_list
