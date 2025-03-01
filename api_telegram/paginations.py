from api_redis.handlers import redis_get_data_from_cache
from api_telegram.callback_data import DetailAction, CacheKey, FavPagination
from api_telegram.keyboards import (
    ItemPaginationBtn,
    builder_kb,
    FavoritePaginationBtn_,
    KeyBoardFactory,
    FavoritePaginationBtn
)
from database.orm import orm_get_favorite


async def paginate_item_list_kb(
        key: str,
        api_page: str,
        page: int,
        item_id: str,
        len_data: int
):
    kb = ItemPaginationBtn(key=key, api_page=api_page, paginator_len=len_data, item_id=item_id)

    if int(api_page) == 1 and int(page) == 1:
        kb.add_buttons(
            [kb.btn('next', int(page) + 1), kb.last_btn()]
        ).add_markups([1, 1])
    elif int(api_page) > 1 and int(page) == 1:
        prev_paginate_page = len(
            await redis_get_data_from_cache(
                CacheKey(key=key, api_page=str(int(api_page) - 1)).pack())
        )
        kb.add_buttons([
            kb.btn('prev', prev_paginate_page),
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

    kb.add_buttons([
        kb.detail('detail', page, DetailAction.go_view),
        kb.btn_text("menu"),
        kb.btn_text("web")
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
    if len_data > 1:
        if navigate == FavPagination.first:
            kb.add_button(kb.pg(page).next_btn(1)).add_markup(1)

        elif navigate == FavPagination.next:
            kb.add_button(kb.pg(page).prev_btn(-1)).add_markup(1)
            if page < len_data:
                kb.add_button(kb.pg(page).next_btn(1)).update_markup(2)

        elif navigate == FavPagination.prev:
            if page > 1:
                kb.add_button(kb.pg(page).prev_btn(-1)).update_markup(2)
            kb.add_button(kb.pg(page).next_btn(1)).add_markup(1)

        kb.add_buttons([kb.delete_btn(), kb.btn_text("menu")]).add_markup(2)

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
