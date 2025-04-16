from typing import Optional

from aiogram import types as t
from aiogram.utils import keyboard

from src.api_telegram import callback_data as cbd
from src.api_telegram.keyboard import factories


class KeyboardManager:
    def __init__(self):
        self.kb: Optional[t.InlineKeyboardMarkup] = None

    async def back(self) -> t.InlineKeyboardMarkup:
        self.kb = factories.BasePaginationBtn()
        self.kb.add_button(self.kb.btn_text("menu")).add_markups([1])
        return self.kb.create_kb()

    async def menu(self):
        self.kb = factories.BasePaginationBtn()
        self.kb.add_buttons(
            [
                self.kb.btn_data(
                    "history",
                    cbd.HistoryCBD(
                        action=cbd.HistoryAction.first,
                        navigate=cbd.Navigation.first,
                        page=1,
                    ).pack(),
                ),
                self.kb.btn_data(
                    "favorite",
                    cbd.FavoriteCBD(
                        action=cbd.FavoriteAction.paginate,
                        navigate=cbd.Navigation.first,
                    ).pack(),
                ),
                self.kb.btn_data(
                    "list_searches",
                    cbd.MonitorCBD(
                        action=cbd.MonitorAction.list,
                        navigate=cbd.Navigation.first,
                        page=1,
                    ).pack(),
                ),
                self.kb.btn_text("help"),
                self.kb.btn_text("search"),
            ]
        ).add_markups([2, 2, 1])
        return self.kb.create_kb()

    async def quantity(self):
        self.kb = factories.BasePaginationBtn()
        self.kb.add_buttons(
            [
                self.kb.btn_text("2"),
                self.kb.btn_text("3"),
                self.kb.btn_text("5"),
                self.kb.btn_text("10"),
            ]
        ).add_markup(2)
        return self.kb.create_kb()

    async def sort(self):
        self.kb = factories.BasePaginationBtn()
        self.kb.add_buttons(
            [
                self.kb.btn_text("default"),
                self.kb.btn_text("salesDesc"),
                self.kb.btn_text("priceDesc"),
                self.kb.btn_text("priceAsc"),
            ]
        ).add_markup(2)
        return self.kb.create_kb()

    # async def item(self, prefix: str, item_id: str, text: str):
    #     return KeyBoardBuilder().builder_id(prefix, item_id, text, (1,))

    async def price_range(self):
        self.kb = factories.BasePaginationBtn()
        self.kb.add_buttons(
            [self.kb.btn_text("price_min"), self.kb.btn_text("price_skip")]
        ).add_markups(
            [
                2,
            ]
        )
        return self.kb.create_kb()

    async def error(self):
        self.kb = factories.BasePaginationBtn()
        self.kb.add_button(self.kb.btn_text("menu"))
        return self.kb.create_kb()

    async def delete(self):
        self.kb = factories.BasePaginationBtn()
        self.kb.add_button(self.kb.btn_data("delete", "delete"))
        return self.kb.create_kb()

    async def video(self) -> t.InlineKeyboardMarkup:
        self.kb = factories.BasePaginationBtn()
        self.kb.add_buttons(
            [self.kb.btn_text("menu"), self.kb.btn_data("video", "instruction")]
        )
        self.kb.add_markup(2)
        return self.kb.create_kb()

    async def back_to_info(self) -> t.InlineKeyboardMarkup:
        self.kb = factories.BasePaginationBtn()
        self.kb.add_button(self.kb.btn_text("help")).add_markups([1])
        return self.kb.create_kb()


kbm = KeyboardManager()

"""
    menu_keyboard = await kb_manager.menu_kb()
    quantity_keyboard = await kb_manager.qnt_kb()
    item_keyboard = await kb_manager.item_kb("prefix", "item_id", "text")
    price_range_keyboard = await kb_manager.price_range_kb()
    error_keyboard = await kb_manager.error_kb()
"""


async def builder_kb(data: list, size: tuple):
    """

    :param data:
    :param size:
    :return:
    """
    return factories.KeyBoardBuilder().builder(data, size)


async def kb_builder(
    size: Optional[tuple] = None, data_list: Optional[list] = None
) -> t.InlineKeyboardMarkup:
    """

    :param size:
    :param data_list:
    :return:
    """
    kb = keyboard.InlineKeyboardBuilder()
    for data in data_list:
        for text, callback in data.items():
            button = t.InlineKeyboardButton(text=text, callback_data=callback)
            kb.add(button)
    return kb.adjust(*size).as_markup()
