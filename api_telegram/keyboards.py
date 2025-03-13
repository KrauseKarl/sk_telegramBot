from typing import Any, TYPE_CHECKING

from aiogram import types
from aiogram.utils import keyboard

from api_telegram.callback_data import *
from core.config import *
from database.orm import *

if TYPE_CHECKING:
    from database.paginator import Paginator
KEYS = {
    "menu": "🏠 menu",
    "web": "🌐",
    "next": "След. ➡️",
    "prev": "⬅️ Пред.",
    "first": "⏪ Первая",
    "last": "Послед.⏩",
    "delete": "❌ удалить",
    "images": "🖼 изображения ",

    "search": "🛒 поиск",
    "history": "📋 история",
    "favorite": "⭐️ избранное",
    "list_searches": "🧭 отслеживание цен",
    "graph": "📊 график цены",

    "default": "📶 по умолчанию",
    "salesDesc": "💰 по продажам",
    "priceDesc": "⬇️ по убыванию",
    "priceAsc": "⬆️ по возрастанию",

    "price_min": "✅ да",
    "price_skip": "🚫 пропустить",

    "review": "💬 комментарии",
    "detail": "ℹ️ подробно",
    "view": "ℹ️ подробно",
    "back": "⬅️ назад",

    "price": "📉 отслеживать цену",

    "2": "2️⃣",
    "3": "3️⃣",
    "5": "5️⃣",
    "10": "🔟"
}

QNT_DATA = [

]


class KeysBuilder:
    def __init__(self, data: dict):
        for key, value in data.items():
            setattr(self, key, value)

    # def __getattr__(self, attr):
    #     return self[attr]

    def to_dict(self):
        return {key: value for (key, value) in self.__dict__.items()}

    def create_btn_callback_data(self, name, callback_data):
        return {getattr(self, name): callback_data}

    def create_btn_text(self, name):
        return {getattr(self, name): name}


# KEYBOARD BUILDER CLASS ###############################################
class KeyBoardBuilder:
    def __init__(self):
        self.kb = keyboard.InlineKeyboardBuilder()
        self.keys = KeysBuilder(KEYS).to_dict()
        self.factory = KeysBuilder(KEYS)

    def builder(
            self, data: list, size: tuple
    ) -> types.InlineKeyboardMarkup:
        """

        :param data:
        :param size:
        :return:
        """
        for data in data:
            for text, data in data.items():
                if isinstance(data, tuple):
                    button = types.InlineKeyboardButton(
                        text=text, url=data[1]
                    )
                else:
                    button = types.InlineKeyboardButton(
                        text=text, callback_data=data
                    )
                self.kb.add(button)
        return self.kb.adjust(*size).as_markup()

    def builder_url(
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
                    text=text, url=callback
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


class KeyBoardFactory(KeyBoardBuilder):

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


class BasePaginationBtn(KeyBoardFactory):
    def __init__(self):
        super().__init__()

    def btn_text(self, name):
        return self.factory.create_btn_text(name)

    def btn_data(self, name, data):
        return self.factory.create_btn_callback_data(name, data)


class ItemPaginationBtn(BasePaginationBtn):
    def __init__(
            self,
            key: str,
            api_page: str | int,
            item_id: str = None,
            paginator_len: str | int = None):
        super().__init__()
        self.key = key
        self.api_page = api_page
        self.item_id = item_id
        self.len = paginator_len
        self.first = 1
        self.callback_data = ItemCBD

    def _btn(self, page, api_page=None):
        return self.callback_data(
            key=self.key,
            api_page=api_page if api_page else self.api_page,
            page=page
        ).pack()

    def _next_page(self, page):
        if page == self.len:
            return str(page)
        return str(int(page) + 1)

    def _prev_page(self, page):
        if page == 1:
            return str(page)
        return str(int(page) - 1)

    def btn(self, name, page, api_page=None):
        return self.btn_data(name, self._btn(page, api_page))

    def first_btn(self):
        return self.btn_data("first", self._btn(self.first))

    def last_btn(self):
        return self.btn_data("last", self._btn(self.len))

    def _detail(self, page: str | int, action):
        return DetailCBD(
            action=action,
            item_id=str(self.item_id),
            key=self.key,
            api_page=self.api_page,
            page=str(page),
            next=self._next_page(page),
            prev=self._prev_page(page),
            first=str(self.first),
            last=str(self.len)
        ).pack()

    def _favorite(self, page: str | int):
        return FavoriteAddCBD(
            action=FavAction.list,
            item_id=str(self.item_id),
            key=self.key,
            api_page=self.api_page,
            next=self._next_page(page),
            prev=self._prev_page(page),
            first=str(self.first),
            last=str(self.len),
            page=str(page),
        ).pack()

    def _comment(self, page: str | int):
        return ReviewCBD(
            action=RevAction.first,
            item_id=str(self.item_id),
            key=self.key,
            api_page=self.api_page,
            next=self._next_page(page),
            prev=self._prev_page(page),
            first=str(self.first),
            last=str(self.len),
            page=str(page),
            navigate=RevNavigate.first,
            review_page=1
        ).pack()

    def _images(self, page: str | int):
        return ImageCBD(
            action=ImgAction.images,
            item_id=str(self.item_id),
            key=self.key,
            api_page=self.api_page,
            page=str(page),
            next=self._next_page(page),
            prev=self._prev_page(page),
            first=str(self.first),
            last=str(self.len),
            navigate=ImgNavigation.first,
            img_page=1
        ).pack()

    def comment(self, page: str | int):
        counter_key("review", self._comment(page))
        return self.btn_data('review', self._comment(page))

    def detail(self, name, page: str | int, action):
        counter_key("detail", self._detail(page, action))
        return self.btn_data(name, self._detail(page, action))

    def favorite(self, page: str | int):
        counter_key("favorite", self._favorite(page))
        return self.btn_data('favorite', self._favorite(page))

    def images(self, page: str | int):
        counter_key("images", self._images(page))
        return self.btn_data("images", self._images(page))


class BaseBtn(BasePaginationBtn):
    def __init__(
            self,
            key: str,
            api_page: str | int,
            item_id: str = None,
            paginator_len: str | int = None,
            page: str | None = None,
            action: DetailsAction | FavoriteAction | ReviewAction | ImagesAction | None = None,
            navigate: Navigation | None = None,
            extra: str | None = None,
            name: str | None = None

    ):
        super().__init__()
        self.data = BaseCBD
        self.key = key
        self.api_page = api_page
        self.item_id = item_id
        self.len = paginator_len
        self.action = action
        self.navigate = navigate
        self.page = page
        self.first = 1
        self.extra = extra
        self.name = name

    def _next_page(self):
        if self.page == self.len:
            return str(self.page)
        return str(int(self.page) + 1)

    def _prev_page(self):
        if self.page == self.first:
            return str(self.page)
        return str(int(self.page) - 1)

    def title(self, name):
        self.name = name
        return self

    def do(self, action):
        self.action = action
        return self

    def nav(self, navigate):
        self.navigate = navigate
        return self

    def pg(self, page):
        self.page = page
        return self

    def extra_page(self, extra):
        self.extra = extra
        return self

    def _callback_data(self):
        return self.data(
            action=self.action,
            navigate=self.navigate,
            item_id=self.item_id,
            key=self.key,
            api_page=self.api_page,
            page=self.page,
            next=self._next_page(),
            prev=self._prev_page(),
            first=str(self.first),
            last=str(self.len),
            extra=self.extra
        ).pack()

    def btn_create(self):
        self._callback_data()


def counter_key(name, data):
    count = 0
    max_len = 64
    # print('=' * 20)
    # print(name.upper().rjust(10, "_"))
    # print(f"[{max_len}] [{count}]")
    for i in str(data).split(':'):
        count += len(i)
        # print(f"[{max_len - count}] [{count}] {len(i)} - {i}")
    # print(f"{name.upper().rjust(10, '_')} TOTAL LEN = [{count}] SAVE RANGE = {max_len - count}")


class ImgPaginationBtn(ItemPaginationBtn):
    def __init__(
            self,
            key: str,
            api_page: str | int,
            item_id: str = None,
            paginator_len: str | int = None,
    ):
        super().__init__(
            key,
            api_page,
            item_id,
            paginator_len,
        )
        self.callback_data = ImageCBD
        self.action = ImgAction
        self.navigate = ImgNavigation
        # self.item_id = item_id
        # self.paginator_len = paginator_len

    def set_callback_data(self, data):
        self.callback_data = data
        return self

    def _call_data(self, page, img_page, navigate):  # page + 1
        return self.callback_data(
            action=self.action.page,
            item_id=self.item_id,
            key=self.key,
            api_page=self.api_page,
            page=str(page),
            next=str(int(page + 1)),
            prev=str(int(page - 1)),
            first=self.first,
            last=self.len,
            navigate=navigate,
            img_page=int(img_page),
        ).pack()

    def next_btn(self, page, img_page):
        return self.btn_data(
            'next',
            self._call_data(page, img_page, navigate=self.navigate.next)
        )

    def prev_btn(self, page, img_page):
        return self.btn_data(
            'prev',
            self._call_data(page, img_page, navigate=self.navigate.prev)
        )


class RevPaginationBtn(ItemPaginationBtn):
    def __init__(
            self,
            key: str,
            api_page: str | int,
            item_id: str = None,
            paginator_len: str | int = None,
    ):
        super().__init__(
            key,
            api_page,
            item_id,
            paginator_len,
        )
        self.data = ReviewCBD
        self.action = RevAction
        self.navigate = RevNavigate
        self.item_id = item_id
        self.paginator_len = paginator_len

    def set_callback_data(self, data):
        self.data = data
        return self

    def _call_data(self, page, review_page, navigate):  # page + 1
        return self.data(
            action=self.action.page,
            item_id=self.item_id,
            key=self.key,
            api_page=self.api_page,
            page=str(page),
            next=str(int(page) + 1),
            prev=str(int(page) - 1),
            first=self.first,
            last=self.len,
            navigate=navigate,
            review_page=int(review_page),
        ).pack()

    def next_btn(self, page, img_page):
        return self.btn_data(
            'next',
            self._call_data(page, img_page, navigate=self.navigate.next)
        )

    def prev_btn(self, page, img_page):
        return self.btn_data(
            'prev',
            self._call_data(page, img_page, navigate=self.navigate.prev)
        )


class PGBtn(ItemPaginationBtn):
    def __init__(
            self,
            key: str,
            api_page: str | int,
            item_id: str = None,
            paginator_len: str | int = None,
            data: Any = None,
            action: Any = None,
            navigate: Any = None,

    ):
        super().__init__(key, api_page, paginator_len, item_id)
        self.paginator_len = paginator_len
        self.callback_data = data
        self.action = action
        self.navigate = navigate

    def _next_call_data(self, page):  # page + 1
        return self.callback_data(
            action=self.action.page,
            navigate=self.navigate.next,
            page=str(int(page + 1))
        ).pack()

    def next(self, page):
        return self.btn_data('next', self._next_call_data(page))

    def _prev_bt_call_data(self, page):  # page - 1
        return self.callback_data(
            action=self.action.page,
            navigate=self.navigate.prev,
            page=str(int(page - 1))
        ).pack()

    def prev(self, page):
        return self.btn_data('prev', self._prev_bt_call_data(page))

    def first(self):
        return self.btn_data('first', 1)

    def last(self):
        return self.btn_data('last', self.paginator_len)


class FavoritePaginationBtn_(BasePaginationBtn):
    def __init__(self, item_id):
        super().__init__()
        self.action = FavAction
        self.navigate = FavPagination
        self.prev = FavPagination.prev
        self.next = FavPagination.next
        self.id = item_id
        self.data = FavoritePageCBD
        self.page = 1

    def next_bt(self, page):  # page + 1
        return self.data(
            action=self.action.page,
            navigate=self.next,
            page=str(int(page + 1))
        ).pack()

    def prev_bt(self, page):  # page - 1
        return self.data(
            action=self.action.page,
            navigate=self.prev,
            page=str(int(page - 1))
        ).pack()

    def delete_btn(self, page, item_id=None):
        return FavoriteDeleteCBD(
            action=self.action.delete,
            item_id=item_id if item_id else self.id,
            page=str(page)
        ).pack()


class FavoritePaginationBtn(BasePaginationBtn):
    def __init__(self, item_id):
        super().__init__()
        self.page = 1
        self.id = item_id
        self.action = FavAction
        self.navigate = FavPagination
        self.call_data = FavoritePageCBD

    def pg(self, page):
        self.page = page
        return self

    def __add__(self, other):
        return self.page + other

    def _btn(self, num, navigate):
        return self.call_data(
            action=self.action.page,
            navigate=navigate,
            page=self.__add__(num)
        ).pack()

    def next_btn(self, num):  # page + 1
        return self.btn_data(
            name='next',
            data=self._btn(num, self.navigate.next)
        )

    def prev_btn(self, num):  # page - 1
        return self.btn_data(
            name='prev',
            data=self._btn(num, self.navigate.prev)
        )

    def delete_btn(self, item_id=None):
        return self.btn_data(
            name='delete',
            data=FavoriteDeleteCBD(
                action=self.action.delete,
                item_id=item_id if item_id else self.id,
                page=self.page
            ).pack()
        )


class PaginationBtn(BasePaginationBtn):
    def __init__(self, action, navigate, call_data, item_id):
        super().__init__()
        self.page = 1
        self.id = item_id
        self.action = action
        self.navigate = navigate
        self.call_data = call_data

    def pg(self, page):
        self.page = page
        return self

    def __add__(self, other):
        return self.page + other

    def _btn(self, num, navigate):
        return self.call_data(
            action=self.action.page,
            navigate=navigate,
            page=self.__add__(num)
        ).pack()

    def next_btn(self, num):  # page + 1
        return self.btn_data(
            name='next',
            data=self._btn(num, self.navigate.next)
        )

    def prev_btn(self, num):  # page - 1
        return self.btn_data(
            name='prev',
            data=self._btn(num, self.navigate.prev)
        )


class ItemSearchPaginationBtn(PaginationBtn):
    def __init__(self, item_id, action, navigate, call_data):
        super().__init__(item_id, action, navigate, call_data)
        self.page = 1
        self.id = item_id
        self.action = action
        self.navigate = navigate
        self.call_data = call_data

    def delete_btn(self, navigate,item_id=None):
        return self.btn_data(
            name='delete',
            data=MonitorCBD(
                action=self.action.delete,
                navigate=navigate,
                item_id=item_id if item_id else self.id,
                page=self.page
            ).pack()
        )

    def _graph_btn(self, navigate, item_id=None):
        return self.call_data(
                action=self.action.graph,
                navigate=navigate,
                item_id=item_id if item_id else self.id,
                page=self.page
            ).pack()

    def graph_btn(self, navigate, item_id=None):
        return self.btn_data('graph', self._graph_btn(navigate, item_id))


class CommentPaginationBtn(FavoritePaginationBtn):
    def __init__(self, item_id):
        super().__init__(item_id)
        self.action = RevAction
        self.navigate = RevNavigate
        self.data = ReviewPageCBD

    def next_bt(self, page):  # page + 1
        return self.data(
            action=self.action.page,
            navigate=self.navigate.next,
            page=str(int(page + 1))
        ).pack()

    def prev_bt(self, page):  # page - 1
        return self.data(
            action=self.action.page,
            navigate=self.navigate.prev,
            page=str(int(page - 1))
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
    return KeyBoardBuilder().builder(data, size)


async def menu_kb():
    """

    :return:
    """
    kb = BasePaginationBtn()
    kb.add_buttons([
        kb.btn_text("search"),
        kb.btn_text("history"),
        kb.btn_data(
            "favorite",
            FavoritePageCBD(action=FavAction.page, navigate=FavPagination.first).pack()
        ),
        kb.btn_data(
            "list_searches",
            MonitorCBD(action=MonitorAction.list, navigate=Navigation.first, page=1).pack()
        )
    ]).add_markups([1, 2])
    print("****** MENU KB", kb)
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
