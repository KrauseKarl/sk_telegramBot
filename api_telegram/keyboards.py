from typing import Any, TYPE_CHECKING, Optional

from aiogram import types
from aiogram.utils import keyboard

from api_redis.handlers import RedisHandler
from database.orm import *
from api_telegram.callback_data import *
from utils.cache_key import counter_key, previous_api_page

if TYPE_CHECKING:
    from database.paginator import Paginator


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
        self.keys = KeysBuilder(config.KEYS).to_dict()
        self.factory = KeysBuilder(config.KEYS)

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


class PaginationBtn(BasePaginationBtn):
    def __init__(self, action, call_data, item_id=None):
        super().__init__()
        self.page = 1
        self.item_id = item_id
        self.action = action
        self.navigate = Navigation
        self.call_data = call_data

    def pg(self, page):
        self.page = page
        return self

    def __add__(self, other):
        if other:
            return self.page + other
        return self.page

    def increase(self, obj):
        if obj:
            return int(obj) + 1

    def decrease(self, obj):
        if obj:
            return int(obj) - 1

    def _btn(self, num, navigate, action, *args, **kwargs):
        return self.call_data(
            action=action,
            navigate=navigate,
            page=self.__add__(num)
        ).pack()

    def next_btn(self, num, sub_page=None, *args, **kwargs):  # page + 1
        return self.btn_data(
            name='next',
            data=self._btn(
                num=num,
                navigate=self.navigate.next,
                action=self.action.paginate,
                sub_page=None,
                *args,
                **kwargs
            )
        )

    def prev_btn(self, num, sub_page=None, *args, **kwargs):  # page - 1
        return self.btn_data(
            name='prev',
            data=self._btn(
                num=num,
                navigate=self.navigate.prev,
                action=self.action.paginate,
                sub_page=None,
                *args,
                **kwargs
            )
        )

    def create_pagination_buttons(self, page, navigate, len_data, sub_page=None, *args, **kwargs):
        if navigate == Navigation.first:
            self.add_button(
                self.pg(page).next_btn(1, self.increase(sub_page), *args, **kwargs)
            )
        elif navigate == Navigation.next:
            self.add_button(
                self.pg(page).prev_btn(-1, self.decrease(sub_page), *args, **kwargs)
            )
            if page < len_data:
                self.add_button(
                    self.pg(page).next_btn(1, self.increase(sub_page), *args, **kwargs)
                )
        elif navigate == Navigation.prev:
            if page > 1:
                self.add_button(
                    self.pg(page).prev_btn(-1, self.decrease(sub_page), *args, **kwargs)
                )
            self.add_button(
                self.pg(page).next_btn(1, self.increase(sub_page), *args, **kwargs)
            )
        self.add_markup(2 if len(self.get_kb()) == 2 else 1)
        return self


class FavoritePaginationBtn(PaginationBtn):
    def __init__(self, action, call_data, item_id):
        super().__init__(action, call_data, item_id)
        self.page = 1
        self.id = item_id
        self.action = action
        self.call_data = call_data

    def _btn(self, num: int, navigate: str, *args, **kwargs):
        return self.call_data(
            action=self.action.paginate,
            navigate=navigate,
            page=self.__add__(num)
        ).pack()

    def next_btn(self, num: int, *args, **kwargs):  # page + 1
        return self.btn_data(
            name='next',
            data=self._btn(num, self.navigate.next, *args, **kwargs)
        )

    def prev_btn(self, num, *args, **kwargs):  # page - 1
        return self.btn_data(
            name='prev',
            data=self._btn(num, self.navigate.prev, *args, **kwargs)
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


class ReviewPaginationBtn(PaginationBtn):
    def __init__(self, action, call_data, item_id, key, api_page, paginator_len):
        super().__init__(action, call_data, item_id)
        self.page = 1
        self.first = 1
        self.key = key
        self.api_page = api_page
        self.len = paginator_len

    def next_btn(self, num, sub_page=None, *args, **kwargs):
        return self.btn_data(
            'next',
            self._btn(num, self.navigate.next, sub_page, *args, **kwargs)
        )

    def prev_btn(self, num, sub_page=None, *args, **kwargs):
        return self.btn_data(
            'prev',
            self._btn(num, self.navigate.prev, sub_page, *args, **kwargs)
        )

    def _btn(self, num: int, navigate: str, sub_page: Optional[int] = None, *args, **kwargs):  # page, sub_page
        return self.call_data(
            action=self.action.paginate,
            item_id=self.item_id,
            key=self.key,
            api_page=self.api_page,
            page=self.page,
            next=self.page + 1,
            prev=self.page - 1,
            first=self.first,
            last=self.len,
            navigate=navigate,
            sub_page=sub_page,
        ).pack()

    def _detail(self, page: int, action: str):
        return DetailCBD(
            action=action,
            item_id=str(self.item_id),
            key=self.key,
            api_page=self.api_page,
            page=page,
            next=page + 1,
            prev=page - 1,
            last=self.len
        ).pack()

    def detail(self, name: str, page: int, action: str):
        return self.btn_data(name, self._detail(page, action))

    def create_pagination_buttons(
            self, page: int, navigate: str, len_data: int, sub_page: Optional[int] = None, *args, **kwargs):
        if navigate == Navigation.first:
            self.add_button(
                self.pg(page).next_btn(1, self.increase(sub_page), *args, **kwargs)
            )
        elif navigate == Navigation.next:
            self.add_button(
                self.pg(page).prev_btn(-1, self.decrease(sub_page), *args, **kwargs)
            )
            if sub_page < len_data:
                self.add_button(
                    self.pg(page).next_btn(1, self.increase(sub_page), *args, **kwargs)
                )
        elif navigate == Navigation.prev:
            if sub_page > 1:
                self.add_button(
                    self.pg(page).prev_btn(-1, self.decrease(sub_page), *args, **kwargs)
                )
            self.add_button(
                self.pg(page).next_btn(1, self.increase(sub_page), *args, **kwargs)
            )
        self.add_markup(2 if len(self.get_kb()) == 2 else 1)
        return self


class MonitorPaginationBtn(PaginationBtn):
    def __init__(self, item_id, action, call_data):
        super().__init__(item_id, action, call_data)
        self.page = 1
        self.item_id = item_id
        self.action = action
        self.call_data = call_data

    def _btn(
            self,
            navigate: str,
            action: Optional[str] = None,
            num: Optional[int] = None,
            *args,
            **kwargs
    ):
        super()._btn(num=num, navigate=navigate, action=action, *args, **kwargs)
        return self.call_data(
            action=action,
            navigate=navigate,
            item_id=self.item_id,
            page=self.__add__(num)
        ).pack()

    def delete_btn(self, navigate: str):
        return self.btn_data(
            'delete',
            self._btn(
                navigate=navigate,
                action=self.action.delete,
                item_id=self.item_id
            )
        )

    def graph_btn(self, navigate: str):
        data = self._btn(
            navigate=navigate,
            action=self.action.graph,
            item_id=self.item_id
        )
        return self.btn_data('graph', data)


class CommentPaginationBtn(PaginationBtn):
    def __init__(self, item_id, action, call_data):
        super().__init__(item_id, action, call_data)
        self.action = ReviewAction
        self.data = ReviewPageCBD

    # def next_bt(self, page):  # page + 1
    #     return self.data(
    #         action=self.action.paginate,
    #         navigate=self.navigate.next,
    #         page=str(int(page + 1))
    #     ).pack()
    #
    # def prev_bt(self, page):  # page - 1
    #     return self.data(
    #         action=self.action.paginate,
    #         navigate=self.navigate.prev,
    #         page=str(int(page - 1))
    #     ).pack()


class HistoryPaginationBtn(PaginationBtn):
    def __init__(self, action, call_data):
        super().__init__(action, call_data)
        self.action = action
        self.page = 1
        self.call_data = call_data

    def _btn(self, num, navigate, *args, **kwargs):
        return self.call_data(
            action=self.action.paginate,
            navigate=navigate,
            page=self.__add__(num)
        ).pack()


class ItemPaginationBtn(BasePaginationBtn):
    def __init__(
            self,
            key: str,
            api_page: str | int,
            item_id: str = None,
            paginator_len: str | int = None):
        super().__init__()
        self.key = key
        self.api_page = int(api_page)
        self.item_id = item_id
        self.len = int(paginator_len)
        self.first = 1
        self.callback_data = ItemCBD

    def _btn(self, page, api_page=None):
        return self.callback_data(
            key=self.key,
            api_page=api_page if api_page else self.api_page,
            page=page
        ).pack()

    def _next_page(self, page: int):
        # if page + 1 < self.len:
        #     return page + 1
        # return self.len + 1

        if page == self.len:
            return page
        return page + 1

    def _prev_page(self, page: int):
        if page == 1:
            return page
        return page - 1

    def btn(self, name: str, page: int, api_page: Optional[int] = None):
        return self.btn_data(name, self._btn(page, api_page))

    def first_btn(self):
        return self.btn_data("first", self._btn(self.first))

    def last_btn(self):
        return self.btn_data("last", self._btn(self.len))

    def _detail(self, page: int, action: str):
        return DetailCBD(
            action=action,
            item_id=str(self.item_id),
            key=self.key,
            api_page=self.api_page,
            page=page,
            next=self._next_page(page),
            prev=self._prev_page(page),
            last=self.len
        ).pack()

    def _favorite(self, page: int):
        return FavoriteAddCBD(
            action=FavoriteAction.list,
            item_id=str(self.item_id),
            key=self.key,
            api_page=self.api_page,
            next=self._next_page(page),
            prev=self._prev_page(page),
            last=self.len,
            page=page,
        ).pack()

    def _comment(self, page: str | int):
        return ReviewCBD(
            action=ReviewAction.first,
            item_id=str(self.item_id),
            key=self.key,
            api_page=self.api_page,
            next=self._next_page(page),
            prev=self._prev_page(page),
            last=self.len,
            page=page,
            navigate=Navigation.first,
            sub_page=1
        ).pack()

    def _images(self, page: int):
        return ImageCBD(
            action=ImagesAction.images,
            item_id=str(self.item_id),
            key=self.key,
            api_page=self.api_page,
            page=page,
            next=self._next_page(page),
            prev=self._prev_page(page),
            last=self.len,
            navigate=Navigation.first,
            sub_page=1
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

    async def create_paginate_buttons(self, page=None):
        if self.api_page == 1 and int(page) == 1:
            self.add_buttons(
                [
                    self.btn('next', int(page) + 1),
                    self.last_btn()
                ]
            ).add_markups([1, 1])

        elif self.api_page > 1 and int(page) == 1:
            # try to find previous item_list in cache
            prev_cache_key = CacheKey(
                key=self.key,
                api_page=str(self.api_page - 1),
                extra='list'
            ).pack()

            redis_handler = RedisHandler()
            prev_list = await redis_handler.get_data(prev_cache_key)
            # if  previous item_list not exist in cache
            # make new request to API
            if prev_list is None:
                #     params = dict(url=config.URL_API_ITEM_LIST)
                #     params = await get_query_from_db(self.key, params)
                #     params['page'] = str(self.api_page)
                #     prev_list = await request_api(params)
                # # finally fins the last page in previous item_list
                # prev_paginate_page = len(prev_list)
                prev_list = await previous_api_page(self.key, self.api_page)
            prev_paginate_page = len(prev_list)

            self.add_buttons([
                self.btn('prev', prev_paginate_page, self.api_page - 1),
                self.btn('next', 2),
                self.last_btn()
            ]).add_markups([2, 1])

        elif self.len > int(page) > 1:
            self.add_buttons([
                self.btn("prev", page - 1 if page - 1 > 1 else 1),
                self.btn("next", page + 1 if page + 1 < self.len else self.len + 1),
                self.first_btn(),
                self.last_btn()
            ]).add_markups([2, 2])

        elif int(page) == self.len:
            # "последняя страница"
            self.add_buttons([
                self.btn("prev", page - 1 if page - 1 != 0 else 1),

                self.btn("next", page + 1),
                self.first_btn(),
            ]).add_markups([2, 1])
###########################################################################################
###########################################################################################
###########################################################################################

# class BaseBtn(BasePaginationBtn):
#     def __init__(
#             self,
#             key: str,
#             api_page: str | int,
#             item_id: str = None,
#             paginator_len: str | int = None,
#             page: str | None = None,
#             action: DetailsAction | FavoriteAction | ReviewAction | ImagesAction | None = None,
#             navigate: Navigation | None = None,
#             extra: str | None = None,
#             name: str | None = None
#
#     ):
#         super().__init__()
#         self.data = BaseCBD
#         self.key = key
#         self.api_page = api_page
#         self.item_id = item_id
#         self.len = paginator_len
#         self.action = action
#         self.navigate = navigate
#         self.page = page
#         self.first = 1
#         self.extra = extra
#         self.name = name
#
#     def _next_page(self):
#         if self.page == self.len:
#             return str(self.page)
#         return str(int(self.page) + 1)
#
#     def _prev_page(self):
#         if self.page == self.first:
#             return str(self.page)
#         return str(int(self.page) - 1)
#
#     def title(self, name):
#         self.name = name
#         return self
#
#     def do(self, action):
#         self.action = action
#         return self
#
#     def nav(self, navigate):
#         self.navigate = navigate
#         return self
#
#     def pg(self, page):
#         self.page = page
#         return self
#
#     def extra_page(self, extra):
#         self.extra = extra
#         return self
#
#     def _callback_data(self):
#         return self.data(
#             action=self.action,
#             navigate=self.navigate,
#             item_id=self.item_id,
#             key=self.key,
#             api_page=self.api_page,
#             page=self.page,
#             next=self._next_page(),
#             prev=self._prev_page(),
#             first=str(self.first),
#             last=str(self.len),
#             extra=self.extra
#         ).pack()
#
#     def btn_create(self):
#         self._callback_data()


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
        self.action = ImagesAction
        self.navigate = Navigation
        # self.item_id = item_id
        # self.paginator_len = paginator_len

    def set_callback_data(self, data):
        self.callback_data = data
        return self

    def _call_data(self, page: int, sub_page: int, navigate: str):  # page + 1
        return self.callback_data(
            action=self.action.paginate,
            item_id=self.item_id,
            key=self.key,
            api_page=self.api_page,
            page=page,
            next=page + 1,
            prev=page - 1,
            last=self.len,
            navigate=navigate,
            sub_page=sub_page,
        ).pack()

    def next_btn(self, page, sub_page):
        return self.btn_data(
            'next',
            self._call_data(page, sub_page, navigate=self.navigate.next)
        )

    def prev_btn(self, page, sub_page):
        return self.btn_data(
            'prev',
            self._call_data(page, sub_page, navigate=self.navigate.prev)
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
        self.action = ReviewAction
        self.navigate = Navigation
        self.item_id = item_id
        self.paginator_len = paginator_len

    def _call_data(self, page, sub_page, navigate):  # page + 1
        return self.data(
            action=self.action.paginate,
            item_id=self.item_id,
            key=self.key,
            api_page=self.api_page,
            page=str(page),
            next=str(int(page) + 1),
            prev=str(int(page) - 1),
            first=self.first,
            last=self.len,
            navigate=navigate,
            sub_page=int(sub_page),
        ).pack()

    def next_btn(self, page, sub_page):
        return self.btn_data(
            'next',
            self._call_data(
                page,
                sub_page,
                navigate=self.navigate.next
            )
        )

    def prev_btn(self, page, sub_page):
        return self.btn_data(
            'prev',
            self._call_data(page, sub_page, navigate=self.navigate.prev)
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
            action=self.action.paginate,
            navigate=self.navigate.next,
            page=str(int(page + 1))
        ).pack()

    def next(self, page):
        return self.btn_data('next', self._next_call_data(page))

    def _prev_bt_call_data(self, page):  # page - 1
        return self.callback_data(
            action=self.action.paginate,
            navigate=self.navigate.prev,
            page=str(int(page - 1))
        ).pack()

    def prev(self, page):
        return self.btn_data('prev', self._prev_bt_call_data(page))

    def first(self):
        return self.btn_data('first', 1)

    def last(self):
        return self.btn_data('last', self.paginator_len)


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