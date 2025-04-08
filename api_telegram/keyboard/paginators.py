from typing import Optional

from api_redis.handlers import RedisHandler
from api_telegram import *
from api_telegram.callback_data import *
from api_telegram.keyboard.factories import KeyBoardFactory, BasePaginationBtn
from utils.cache_key import previous_api_page, counter_key


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

    def next_btn(self, num: int = 1, sub_page=None, *args, **kwargs):  # page + 1
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

    def prev_btn(self, num: int = -1, sub_page=None, *args, **kwargs):  # page - 1
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
        self.item_id = item_id
        self.action = action
        self.call_data = call_data

    def _btn(self, num: int, navigate: str, *args, **kwargs):
        return self.call_data(
            action=self.action.paginate,
            navigate=navigate,
            page=self.__add__(num),
            item_id=self.item_id
        ).pack()

    def next_btn(self, num: int = 1, *args, **kwargs):  # page + 1
        return self.btn_data(
            name='next',
            data=self._btn(num, self.navigate.next, *args, **kwargs)
        )

    def prev_btn(self, num: int = -1, *args, **kwargs):  # page - 1
        return self.btn_data(
            name='prev',
            data=self._btn(num, self.navigate.prev, *args, **kwargs)
        )

    def delete_btn(self, navigate, item_id=None):
        return self.btn_data(
            name='delete',
            data=FavoriteDeleteCBD(
                action=self.action.delete,
                navigate=navigate,
                item_id=self.item_id,
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


class ImagePaginationBtn(PaginationBtn):
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

    def target_btn(self, navigate: str):
        data = self._btn(
            navigate=navigate,
            action=self.action.target,
            item_id=self.item_id
        )
        return self.btn_data('target', data)


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
            api_page: int,
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
            navigate=Navigation.first,
            item_id=str(self.item_id),
            key=self.key,
            api_page=self.api_page,
            page=page,
            next=self._next_page(page),
            prev=self._prev_page(page),
            last=self.len,
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
                api_page=self.api_page - 1,
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
                prev_list = await previous_api_page(self.key, self.api_page - 1)
            prev_paginate_page = len(prev_list)

            self.add_buttons([
                self.btn(name='prev', page=prev_paginate_page, api_page=self.api_page - 1),
                self.btn(name='next', page=2),
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
