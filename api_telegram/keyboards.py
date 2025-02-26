from typing import Any, Coroutine, TYPE_CHECKING

from aiogram import types
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
from aiogram.utils import keyboard

from api_redis.handlers import redis_get_data_from_cache
from api_telegram.callback_data import *
from core.config import *
from database.orm import orm_get_favorite, orm_get_favorite_list
from database.pagination import Paginator

if TYPE_CHECKING:
    from database.pagination import Paginator

SORT_DATA = [
    {"📶 по умолчанию": "default"},
    {"💰 по продажам": "salesDesc"},
    {"⬇️ по убыванию": "priceDesc"},
    {"️⬆️по возрастанию": "priceAsc"},
]
MENU_DATA = [
    {"🛒 поиск товара": "search"},
    # {"🧾 поиск категории": "category"},
    {"📋 история команд": "history"},
    {"️⭐️ избранное": FavoritePageCBD(
        action=FavAction.page,
        navigate=FavPagination.first
    ).pack()},
]

QNT_DATA = [
    {"2️⃣": "2"},
    {"3️⃣": "3"},
    {"5️⃣": "5"},
    {"🔟": "10"}
]


# KEYBOARD BUILDER CLASS ###############################################
class KB:
    def __init__(self):
        self.kb = keyboard.InlineKeyboardBuilder()

    def builder(
            self, data: list, size: tuple
    ) -> types.InlineKeyboardMarkup:
        """

        :param data:
        :param size:
        :return:
        """
        for data in data:
            for text, callback in data.items():
                button = types.InlineKeyboardButton(
                    text=text, callback_data=callback
                )
                self.kb.add(button)
        return self.kb.adjust(*size).as_markup()

    def builder_id(
            self, prefix: str, uid: str, text: str, size: tuple
    ) -> types.InlineKeyboardMarkup:
        """

        :param prefix:
        :param uid:
        :param text:
        :param size:
        :return:
        """
        callback = "{0}_{1}".format(prefix, uid)
        button = types.InlineKeyboardButton(text=text, callback_data=callback)
        self.kb.add(button)
        return self.kb.adjust(*size).as_markup()


class PaginationKB(KB):

    def __init__(self):
        super().__init__()
        self.keyboard_list = []
        self.markup = []

    def get_kb(self):
        return self.keyboard_list

    def get_markup(self):
        return tuple(self.markup)

    def add_button_first(self, obj):
        self.keyboard_list.insert(0, obj)
        return self

    def add_button(self, obj):
        self.keyboard_list.append(obj)
        return self

    def add_buttons(self, objs: list):
        self.keyboard_list.extend(objs)
        return self

    def add_markup(self, obj):
        self.markup.append(obj)
        return self

    def update_markup(self, obj):
        self.markup.pop()
        self.add_markup(obj)
        return self

    def add_markups(self, objs: list):
        self.markup.extend(objs)
        return self

    def add_markup_first(self, obj):
        self.markup.insert(0, obj)
        return self

    def create_kb(self):
        return self.builder(
            self.get_kb(),
            self.get_markup()
        )


class DetailPaginationBtn:
    def __init__(self, data: FavoriteAddCBD):
        self.action = DetailAction.view,
        self.data = data

    def detail(self):
        return DetailCBD(
            action=self.action,
            item_id=str(self.data.item_id),
            key=self.data.key,
            api_page=self.data.api_page,
            page=str(self.data.page),
            next=str(self.data.page),
            prev=str(self.data.page),
            first=str(self.data.first),
            last=str(self.data.last)
        ).pack()


class ItemPaginationBtn:
    def __init__(self, key: str, api_page: str, paginator_len: int = None):
        self.key = key
        self.api_page = api_page
        self.len = paginator_len
        self.first = 1
        self.keyboard_list = []

    def btn(self, page):
        return ItemCBD(key=self.key, api_page=self.api_page, page=page).pack()

    def first_btn(self):
        return ItemCBD(key=self.key, api_page=self.api_page, page=self.first).pack()

    def last_btn(self):
        return ItemCBD(key=self.key, api_page=self.api_page, page=self.len).pack()

    def detail(self, page: str | int, item_id: str):
        return DetailCBD(
            action=DetailAction.view,
            item_id=str(item_id),
            key=self.key,
            api_page=self.api_page,
            page=str(page),
            next=str(int(page) + 1),
            prev=str(int(page) - 1),
            first=str(self.first),
            last=str(self.len)
        ).pack()

    def favorite(self, page: str | int, item_id: str):
        return FavoriteAddCBD(
            action=FavAction.list,
            item_id=str(item_id),
            key=self.key,
            api_page=self.api_page,
            next=str(int(page) + 1),
            prev=str(int(page) - 1),
            first=str(self.first),
            last=str(self.len),
            page=str(page),
        ).pack()


class FavoritePaginationBtn:
    def __init__(self, item_id):
        self.action = FavAction
        self.navigate = FavPagination
        self.id = item_id

    def next_bt(self, page):  # page + 1
        return FavoritePageCBD(
            action=self.action.page,
            navigate=self.navigate.next,
            page=str(int(page + 1))
        ).pack()

    def prev_bt(self, page):  # page - 1
        return FavoritePageCBD(
            action=self.action.page,
            navigate=self.navigate.prev,
            page=str(int(page - 1))
        ).pack()

    def delete_btn(self, page, item_id=None):
        return FavoriteDeleteCBD(
            action=self.action.delete,
            item_id=item_id if item_id else self.id,
            page=str(page)
        ).pack()


# KEYBOARD BUILDER FUNC ###############################################
async def kb_builder(
        size: tuple = None, data_list: list = None
) -> types.InlineKeyboardMarkup:
    """

    :param size:
    :param data_list:
    :return:
    """
    kb = keyboard.InlineKeyboardBuilder()
    for data in data_list:
        for text, callback in data.items():
            button = types.InlineKeyboardButton(
                text=text,
                callback_data=callback
            )
            kb.add(button)
    return kb.adjust(*size).as_markup()


# KEYBOARD GENERAL BUILDER ################################################
async def builder_kb(data: list, size: tuple):
    """

    :param data:
    :param size:
    :return:
    """
    return KB().builder(data, size)


async def menu_kb():
    """

    :return:
    """
    return await builder_kb(MENU_DATA, (1, 2))


async def sort_kb():
    """

    :return:
    """
    return await builder_kb(SORT_DATA, (2, 2,))


async def qnt_kb():
    """

    :return:
    """
    return await builder_kb(QNT_DATA, (2, 2,))


async def item_kb(prefix: str, item_id: str, text: str):
    """

    :param prefix:
    :param item_id:
    :param text:
    :return:
    """
    return KB().builder_id(prefix, item_id, text, (1,))


async def item_kb_2(data: list):
    """

    :param data:
    :return:
    """
    return KB().builder(data, (2,))


async def price_range_kb():
    return await kb_builder(
        (2,),
        [{"✅ да": "price_min"}, {"🚫 пропустить": "price_skip"}]
    )


async def error_kb():
    return await builder_kb([{"🏠 back menu": "menu"}], (1,))



async def paginate_item_list_kb(
        key: str,
        api_page: str,
        page: int,
        item_id: str,
        len_data: int
):
    btn_set = ItemPaginationBtn(key=key, api_page=api_page, paginator_len=len_data)
    kb = PaginationKB()
    if int(api_page) == 1 and int(page) == 1:
        buttons = [
            {"➡️ След.": btn_set.btn(int(page) + 1)},
            {"⏩ Послед.": btn_set.last_btn()}
        ]
        kb.add_buttons(buttons)
        kb.add_markups([1, 1])
    elif int(api_page) > 1 and int(page) == 1:
        prev_paginate_page = len(
            await redis_get_data_from_cache(CacheKey(key=key, api_page=str(int(api_page) - 1)).pack()))
        buttons = [
            {"⬅️ Пред.": btn_set.btn(prev_paginate_page)},
            {"➡️ След": btn_set.btn(2)},
            {"⏩ Послед.": btn_set.last_btn()}
        ]
        kb.add_buttons(buttons)
        kb.add_markups([2, 1])
    elif len_data > int(page) > 1:
        buttons = [
            {"⬅️ Пред.": btn_set.btn(str(page - 1 if page - 1 > 1 else 1))},
            {"➡️ След": btn_set.btn(str(page + 1 if page + 1 < len_data else len_data + 1))},
            {"⏪ Перв.": btn_set.first_btn()},
            {"⏩ Послед.": btn_set.last_btn()}
        ]
        kb.add_buttons(buttons)
        kb.add_markups([2, 2])
    elif int(page) == len_data:
        # "последняя страница"
        buttons = [
            {"⬅️ Пред.": btn_set.btn(str(page - 1 if page - 1 != 0 else 1))},
            {"➡️ След": btn_set.btn(str(page + 1))},
            {"⏪ Перв.": btn_set.first_btn()},
        ]
        kb.add_buttons(buttons)
        kb.add_markups([2, 1])

    buttons = [
        {"ℹ️ подробно": btn_set.detail(page, item_id)},
        {"🏠 меню": "menu"},
        {"🌐": "menu"}
    ]
    kb.add_buttons(buttons)
    kb.add_markup(3)
    is_favorite = await orm_get_favorite(item_id)
    if is_favorite is None:
        kb.add_button({"⭐️ в избранное": btn_set.favorite(page, item_id)})
        kb.update_markup(4)

    return await builder_kb(kb.get_kb(), size=kb.get_markup())


async def paginate_favorite_list_kb(page: int, item_id, navigate: str, len_data: int):
    """

    :param page:
    :param item_id:
    :param navigate:
    :param len_data:
    :return:
    """
    kb = PaginationKB()
    btn = FavoritePaginationBtn(item_id)

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

    buttons = [{"❌ удалить": btn.delete_btn(page, item_id)}, {"🏠 menu": "menu"}]
    kb.add_buttons(buttons).add_markup(2)
    print('8888', kb.get_markup())
    return kb.create_kb()


async def paginate_favorite_delete_kb(
        page: int,
        len_data: int,
        item_id
):
    keyboard_list = []
    if page == 0:
        page += 1
        if len_data == 0:
            pass
        keyboard_list.append({"След. ➡️": await next_button(page)})
    elif page == 1:
        keyboard_list.append({"След. ➡️": await next_button(page)})
    else:
        if len_data > 1:
            keyboard_list.extend(
                [
                    {"⬅️ Пред.": await prev_button(page)},
                    {"След. ➡️": await next_button(page)}
                ]
            )
    keyboard_list.append({"❌ удалить": await delete_button(page - 1, item_id)})
    return keyboard_list
