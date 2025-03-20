from api_telegram.callback_data import (
    FavoriteCBD,
    MonitorCBD,
    Navigation,
    MonitorAction,
    HistoryCBD,
    HistoryAction, FavoriteAction
)
from api_telegram.keyboard.factories import KeyBoardBuilder
from api_telegram.keyboards import BasePaginationBtn


class KeyboardManager:
    def __init__(self):
        self.kb = None

    async def back(self):
        self.kb = BasePaginationBtn()
        self.kb.add_button(
            self.kb.btn_text("menu")
        ).add_markups([1])

        return self.kb.create_kb()

    async def menu(self):
        self.kb = BasePaginationBtn()
        self.kb.add_buttons([
            self.kb.btn_data(
                "history",
                HistoryCBD(
                    action=HistoryAction.first,
                    navigate=Navigation.first,
                    page=1
                ).pack()
            ),
            self.kb.btn_data(
                "favorite",
                FavoriteCBD(
                    action=FavoriteAction.page,
                    navigate=Navigation.first
                ).pack()
            ),
            self.kb.btn_data(
                "list_searches",
                MonitorCBD(
                    action=MonitorAction.list,
                    navigate=Navigation.first,
                    page=1
                ).pack()
            ),
            self.kb.btn_text("help"),
            self.kb.btn_text("search"),
        ]).add_markups([2, 2, 1])
        return self.kb.create_kb()

    async def quantity(self):
        self.kb = BasePaginationBtn()
        self.kb.add_buttons([
            self.kb.btn_text("2"),
            self.kb.btn_text("3"),
            self.kb.btn_text("5"),
            self.kb.btn_text("10")
        ]).add_markups([2, ])
        return self.kb.create_kb()

    async def sort(self):
        self.kb = BasePaginationBtn()
        self.kb.add_buttons([
            self.kb.btn_text("default"),
            self.kb.btn_text("salesDesc"),
            self.kb.btn_text("priceDesc"),
            self.kb.btn_text("priceAsc")
        ]).add_markups([2, ])
        return self.kb.create_kb()

    # async def item(self, prefix: str, item_id: str, text: str):
    #     return KeyBoardBuilder().builder_id(prefix, item_id, text, (1,))

    async def price_range(self):
        self.kb = BasePaginationBtn()
        self.kb.add_buttons([
            self.kb.btn_text("price_min"),
            self.kb.btn_text("price_skip")
        ]).add_markups([2, ])
        return self.kb.create_kb()

    async def error(self):
        self.kb = BasePaginationBtn()
        self.kb.add_buttons([
            self.kb.btn_text("menu"),
        ]).add_markups([1, ])
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
    return KeyBoardBuilder().builder(data, size)


async def menu_kb():
    """

    :return:
    """
    kb = BasePaginationBtn()
    kb.add_buttons([
        kb.btn_data(
            "history",
            HistoryCBD(
                action=HistoryAction.first,
                navigate=Navigation.first,
                page=1
            ).pack()
        ),
        kb.btn_data(
            "favorite",
            FavoriteCBD(
                action=FavoriteAction.page,
                navigate=Navigation.first
            ).pack()
        ),
        kb.btn_data(
            "list_searches",
            MonitorCBD(
                action=MonitorAction.list,
                navigate=Navigation.first,
                page=1
            ).pack()
        ),
        kb.btn_text("search")
    ]).add_markups([3, 1])

    return kb.create_kb()


async def sort_kb():
    """

    :return:
    """
    kb = BasePaginationBtn()
    kb.add_buttons([
        kb.btn_text("default"),
        kb.btn_text("salesDesc"),
        kb.btn_text("priceDesc"),
        kb.btn_text("priceAsc")
    ]).add_markups([2, 2])
    return kb.create_kb()


async def qnt_kb():
    """

    :return:

    """
    kb = BasePaginationBtn()
    kb.add_buttons([
        kb.btn_text("2"),
        kb.btn_text("3"),
        kb.btn_text("5"),
        kb.btn_text("10")
    ]).add_markups([2, ])
    return kb.create_kb()


async def item_kb(prefix: str, item_id: str, text: str):
    """

    :param prefix:
    :param item_id:
    :param text:
    :return:
    """
    return KeyBoardBuilder().builder_id(prefix, item_id, text, (1,))


async def price_range_kb():
    kb = BasePaginationBtn()
    kb.add_buttons([
        kb.btn_text("price_min"),
        kb.btn_text("price_skip")
    ]).add_markups([2, ])
    return kb.create_kb()


async def error_kb():
    kb = BasePaginationBtn()
    kb.add_buttons([
        kb.btn_text("menu"),
    ]).add_markups([1, ])
    return kb.create_kb()
