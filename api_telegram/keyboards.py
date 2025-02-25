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


# async def main_keyboard():
#     kb_list = [[KeyboardButton(text="Menu")]]
#     # if user_telegram_id in admins:
#     #     kb_list.append([KeyboardButton(text="⚙️ Админ панель")])
#     kb = ReplyKeyboardMarkup(
#         keyboard=kb_list,
#         resize_keyboard=True,
#         # one_time_keyboard=True
#         input_field_placeholder='stars'
#     )
#     return kb


async def get_paginate_item_kb(
        key: str,
        api_page: str,
        paginate_page: int,
        item: dict,
        paginator: Paginator
):
    keyboard_list = []
    markup_size = []

    if int(api_page) == 1 and int(paginate_page) == 1:
        # "1-й запрос и 1-я страница" print("⌨️1й запрос и 1я страница ")
        next_kb = ItemCBD(key=key, api_page=api_page, paginate_page=int(paginate_page) + 1).pack()
        last_kb = ItemCBD(key=key, api_page=api_page, paginate_page=str(paginator.pages)).pack()
        keyboard_list.extend(
            [
                {"След. ➡️": next_kb},
                {"После. ⏩": last_kb}
            ]
        )
        markup_size = [1, 1]
    elif int(api_page) > 1 and int(paginate_page) == 1:
        # "Следующий запрос и 1-я страница" # print("⌨️Следующий запрос и 1я страница")
        next_kb = ItemCBD(key=key, api_page=api_page, paginate_page=2).pack()
        last_kb = ItemCBD(key=key, api_page=api_page, paginate_page=str(paginator.pages)).pack()
        prev_paginate_page = len(
            await redis_get_data_from_cache(CacheKey(key=key, api_page=str(int(api_page) - 1)).pack()))
        prev_kb = ItemCBD(key=key, api_page=str(int(api_page) - 1), paginate_page=prev_paginate_page).pack()
        keyboard_list.extend(
            [
                {"⬅️ Пред.": prev_kb},
                {"След. ➡️": next_kb},
                {" После. ⏩": last_kb}
            ]
        )
        markup_size = [2, 1]
    elif paginator.pages > int(paginate_page) > 1:
        # "следующая страница" # print("⌨️ следующая страница")
        next_page = str(paginate_page + 1 if paginate_page + 1 < paginator.pages else paginator.pages + 1)
        next_kb = ItemCBD(key=key, api_page=api_page, paginate_page=next_page).pack()
        last_kb = ItemCBD(key=key, api_page=api_page, paginate_page=str(paginator.pages)).pack()
        prev_page = str(paginate_page - 1 if paginate_page - 1 > 1 else 1)
        prev_kb = ItemCBD(key=key, api_page=api_page, paginate_page=prev_page).pack()
        first_kb = ItemCBD(key=key, api_page=api_page, paginate_page=str(1)).pack()
        keyboard_list.extend(
            [
                {"⬅️ Пред.": prev_kb},
                {"След. ➡️": next_kb},
                {"⏪ Первая": first_kb},
                {"После. ⏩": last_kb}
            ]
        )
        markup_size = [2, 2]
    elif int(paginate_page) == paginator.pages:
        # "последняя страница"  print("⌨️ последняя страница ")
        next_kb = ItemCBD(key=key, api_page=api_page, paginate_page=str(paginate_page + 1)).pack()
        prev_page = str(paginate_page - 1 if paginate_page - 1 != 0 else 1)
        prev_kb = ItemCBD(key=key, api_page=api_page, paginate_page=prev_page).pack()
        first_kb = ItemCBD(key=key, api_page=api_page, paginate_page=str(1)).pack()
        keyboard_list.extend(
            [
                {"⬅️ Пред.": prev_kb},
                {"След. ➡️": next_kb},
                {"⏪ Первая": first_kb},
            ]
        )
        markup_size = [2, 1]

    view_detail_callback = DetailCBD(
        action=DetailAction.view,
        item_id=str(item['item']['itemId']),
        key=key,
        api_page=api_page,
        paginate_page=str(paginate_page),
        next=str(paginate_page + 1),
        prev=str(paginate_page - 1),
        first=str(1),
        last=str(paginator.pages)
    ).pack()
    keyboard_list.extend(
        [
            {"ℹ️ подробно": view_detail_callback},
            {"🏠 menu": "menu"},
            {"🌐": "menu"}
        ]
    )
    markup_size.append(3)
    item_is_favorite = await orm_get_favorite(item['item']['itemId'])

    if item_is_favorite is None:
        add_to_favorite_call_back = FavoriteAddCBD(
            action=FavAction.list,
            item_id=str(item['item']['itemId']),
            key=key,
            api_page=api_page,
            paginate_page=str(paginate_page),
            next=str(paginate_page + 1),
            prev=str(paginate_page - 1),
            first=str(1),
            last=str(paginator.pages)
        ).pack()
        keyboard_list.extend([{"⭐️ в избранное": add_to_favorite_call_back}])
        markup_size.pop()
        markup_size.append(4)

    return await builder_kb(keyboard_list, size=tuple(markup_size))


async def get_paginate_favorite_kb(
        page: int,
        paginator,
        item_id,
        navigate: str,
        len_data: int
):
    """

    :param page:
    :param paginator:
    :param item_id:
    :param navigate:
    :param len_data:
    :return:
    """
    delete_button = FavoriteDeleteCBD(action=FavAction.delete, item_id=item_id, page=str(page)).pack()
    keyboard_list = [{"❌ удалить": delete_button}]
    prev_button = None
    next_button = None

    if len_data > 1:
        if navigate == FavPagination.first:
            next_button = FavoritePageCBD(
                action=FavAction.page, navigate=FavPagination.next, page=page + 1
            ).pack()
        elif navigate == FavPagination.next:
            prev_button = FavoritePageCBD(
                action=FavAction.page, navigate=FavPagination.prev, page=page - 1
            ).pack()
            if page < int(paginator.pages):
                next_button = FavoritePageCBD(
                    action=FavAction.page, navigate=FavPagination.next, page=page + 1
                ).pack()
        elif navigate == FavPagination.prev:
            if page > 1:
                prev_button = FavoritePageCBD(
                    action=FavAction.page, navigate=FavPagination.prev, page=page - 1
                ).pack()
            next_button = FavoritePageCBD(
                action=FavAction.page, navigate=FavPagination.prev, page=page + 1
            ).pack()
    if next_button:
        keyboard_list.insert(0, {"След. ➡️": next_button})
    if prev_button:
        keyboard_list.insert(0, {"⬅️ Пред.": prev_button})

    return keyboard_list


async def get_paginate_favorite_delete(
        page: int,
        paginator: Paginator,
        item_id
):
    keyboard_list = []
    if page == 0:
        page += 1
        if len(paginator.get_page()) == 0:
           pass
        next_button = FavoritePageCBD(action=FavAction.page, navigate=FavPagination.next, page=page + 1).pack()
        keyboard_list.append({"След. ➡️": next_button})
    elif page == 1:
        next_button = FavoritePageCBD(action=FavAction.page, navigate=FavPagination.next, page=page + 1).pack()
        keyboard_list.append({"След. ➡️": next_button})
    else:
        if int(paginator.pages) > 1:
            prev_button = FavoritePageCBD(action=FavAction.page, navigate=FavPagination.prev, page=page - 1).pack()
            keyboard_list.append({"⬅️ Пред.": prev_button})
            next_button = FavoritePageCBD(action=FavAction.page, navigate=FavPagination.next, page=page + 1).pack()
            keyboard_list.append({"След. ➡️": next_button})
    delete_button = FavoriteDeleteCBD(action=FavAction.delete, item_id=item_id, page=str(page - 1)).pack()
    keyboard_list.append({"❌ удалить": delete_button})

    return keyboard_list
