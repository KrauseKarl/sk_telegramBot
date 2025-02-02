from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from config import *
main_keyboard = InlineKeyboardMarkup(
    row_width=3,
    inline_keyboard=[
        [
            InlineKeyboardButton(text="поиск товара", callback_data="search"),
            InlineKeyboardButton(text="поиск категории", callback_data="category"),
        ],
        [
            InlineKeyboardButton(text="история команд", callback_data="history"),
        ]
    ],
)

sort_keyboard = InlineKeyboardMarkup(
    row_width=3,
    inline_keyboard=[
        [
            InlineKeyboardButton(text="по умолчанию", callback_data="default"),
        ],
        [
            InlineKeyboardButton(text="️️⬇️ по убыванию", callback_data="priceDesc"),
            InlineKeyboardButton(text="⬆️ по возрастанию", callback_data="priceAsc"),
        ],
        [
            InlineKeyboardButton(text="💰 по продажам", callback_data="salesDesc"),
        ]
    ],
)


async def get_qnt_kb():
    keyboard = InlineKeyboardBuilder()
    for value in BTNS:
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
