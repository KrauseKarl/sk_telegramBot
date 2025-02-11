from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

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
    {"️⭐️ избранное": "favorites"},
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
        self.kb = InlineKeyboardBuilder()

    def builder(self, data: list, size: tuple):
        for data in data:
            for text, callback in data.items():
                button = InlineKeyboardButton(text=text, callback_data=callback)
                self.kb.add(button)
        return self.kb.adjust(*size).as_markup()

    def builder_id(self, prefix: str, uid: str, text: str, size: tuple):
        callback = "{0}_{1}".format(prefix, uid)
        button = InlineKeyboardButton(text=text, callback_data=callback)
        self.kb.add(button)
        return self.kb.adjust(*size).as_markup()


# KEYBOARD BUILDER FUNC ###############################################
async def kb_builder(size: tuple = None, data_list: list = None):
    kb = InlineKeyboardBuilder()
    for data in data_list:
        for text, callback in data.items():
            button = InlineKeyboardButton(text=text, callback_data=callback)
            kb.add(button)
    return kb.adjust(*size).as_markup()


# DEPRECATED ##########################################################
async def __item_kb(item_id: str):
    call = "item_{0}".format(item_id)
    return kb_builder(size=(2, 2, 1,), data_list=[{"подробно": call}])


async def __kb_menu():
    return await kb_builder(size=(2, 2, 1,), data_list=MENU_DATA)


# KEYBOARD GENERAL BUILDER ################################################
async def builder_kb(data, size):
    return KB().builder(data, size)


kb_menu = builder_kb(MENU_DATA, (2,))
kb_sort = builder_kb(SORT_DATA, (2,))
kb_qnt = builder_kb(QNT_DATA, (2,))


async def menu_kb():
    return await builder_kb(MENU_DATA, (2,))


async def sort_kb():
    return await builder_kb(SORT_DATA, (2, 2,))


async def qnt_kb():
    return await builder_kb(QNT_DATA, (2, 2,))


async def item_kb(prefix: str, item_id: str, text: str):
    return KB().builder_id(prefix, item_id, text, (1,))


async def item_kb_2(data: list):
    return KB().builder(data, (2,))


# menu_kb = InlineKeyboardMarkup(
#     row_width=3,
#     inline_keyboard=[
#         [
#             InlineKeyboardButton(text="🛒 поиск товара", callback_data="search"),
#             InlineKeyboardButton(text="🧾 поиск категории", callback_data="category"),
#         ],
#         [
#             InlineKeyboardButton(text="📋 история команд", callback_data="history"),
#         ],
#         [
#             InlineKeyboardButton(text="⭐️ избранное", callback_data="favorite"),
#         ]
#     ],
# )


# sort_kb = InlineKeyboardMarkup(
#     row_width=3,
#     inline_keyboard=[
#         [
#             InlineKeyboardButton(text="по умолчанию", callback_data="default"),
#         ],
#         [
#             InlineKeyboardButton(text="️️⬇️ по убыванию", callback_data="priceDesc"),
#             InlineKeyboardButton(text="⬆️ по возрастанию", callback_data="priceAsc"),
#         ],
#         [
#             InlineKeyboardButton(text="💰 по продажам", callback_data="salesDesc"),
#         ]
#     ],
# )


async def get_qnt_kb():
    keyboard = InlineKeyboardBuilder()
    for value in QNT:
        keyboard.add(InlineKeyboardButton(text=value, callback_data=value))
    return keyboard.adjust(*(4,)).as_markup()


async def item_kb(item_id: str):
    call = "item_{0}".format(item_id)
    item_keyboard = InlineKeyboardMarkup(
        row_width=1,
        inline_keyboard=[
            [
                InlineKeyboardButton(text="подробно", callback_data=call),
            ]
        ],
    )
    return item_keyboard
