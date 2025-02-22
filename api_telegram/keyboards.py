from typing import Any, Coroutine

from aiogram import types
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
from aiogram.utils import keyboard

from api_telegram.callback_data import *
from core.config import *

SORT_DATA = [
    {"по умолчанию": "default"},
    {"💰 по продажам": "salesDesc"},
    {"⬇️ по убыванию": "priceDesc"},
    {"️ ⬆️по возрастанию": "priceAsc"},
]
MENU_DATA = [
    {"🛒 поиск товара": "search"},
    {"🧾 поиск категории": "category"},
    {"📋 история команд": "history"},
    {"️⭐️ избранное": FavoritePageCBD(action=FavAction.page, page=FavPagination.first).pack()},
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
    return await builder_kb(MENU_DATA, (2,))


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


async def error_kb():
    return await builder_kb([{"🏠 back menu": "menu"}], (1,))


async def main_keyboard():
    kb_list = [[KeyboardButton(text="Menu")]]
    # if user_telegram_id in admins:
    #     kb_list.append([KeyboardButton(text="⚙️ Админ панель")])
    kb = ReplyKeyboardMarkup(
        keyboard=kb_list,
        resize_keyboard=True,
        # one_time_keyboard=True
        input_field_placeholder='stars'
    )
    return kb
