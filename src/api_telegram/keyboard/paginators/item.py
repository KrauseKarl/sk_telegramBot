from typing import Optional

from src.api_redis import RedisHandler
from src.api_telegram import (
    CacheKey,
    DetailCBD,
    FavoriteAction,
    FavoriteAddCBD,
    ImageCBD,
    ImagesAction,
    ItemCBD,
    Navigation,
    ReviewAction,
    ReviewCBD,
)
from src.api_telegram.keyboard import factories
from src.utils import cache_key


class ItemPaginationBtn(factories.BasePaginationBtn):
    def __init__(
        self,
        key: str,
        api_page: int,
        item_id: str = None,
        paginator_len: str | int = None,
    ):
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
            page=page,
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
            last=self.len,
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
            sub_page=1,
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
            sub_page=1,
        ).pack()

    def comment(self, page: str | int):
        cache_key.counter_key("review", self._comment(page))
        return self.btn_data("review", self._comment(page))

    def detail(self, name, page: str | int, action):
        cache_key.counter_key("detail", self._detail(page, action))
        return self.btn_data(name, self._detail(page, action))

    def favorite(self, page: str | int):
        cache_key.counter_key("favorite", self._favorite(page))
        return self.btn_data("favorite", self._favorite(page))

    def images(self, page: str | int):
        cache_key.counter_key("images", self._images(page))
        return self.btn_data("images", self._images(page))

    async def create_paginate_buttons(self, page=None):
        if self.api_page == 1 and int(page) == 1:
            self.add_buttons(
                [self.btn("next", int(page) + 1), self.last_btn()]
            ).add_markups([1, 1])

        elif self.api_page > 1 and int(page) == 1:
            # try to find previous item_list in cache
            prev_cache_key = CacheKey(
                key=self.key, api_page=self.api_page - 1, extra="list"
            ).pack()
            redis_handler = RedisHandler()
            prev_list = await redis_handler.get_data(prev_cache_key)
            # if  previous item_list ⚠️ not exist in cache
            # make new request to API
            if prev_list is None:
                # finally fins the last page in previous item_list
                # prev_paginate_page = len(prev_list)
                prev_list = await cache_key.previous_api_page(
                    self.key, self.api_page - 1
                )
            prev_paginate_page = len(prev_list)

            self.add_buttons(
                [
                    self.btn(
                        name="prev",
                        page=prev_paginate_page,
                        api_page=self.api_page - 1,
                    ),
                    self.btn(name="next", page=2),
                    self.last_btn(),
                ]
            ).add_markups([2, 1])

        elif self.len > int(page) > 1:
            self.add_buttons(
                [
                    self.btn("prev", page - 1 if page - 1 > 1 else 1),
                    self.btn(
                        "next",
                        page + 1 if page + 1 < self.len else self.len + 1,
                    ),
                    self.first_btn(),
                    self.last_btn(),
                ]
            ).add_markups([2, 2])

        elif int(page) == self.len:
            # "последняя страница"
            self.add_buttons(
                [
                    self.btn("prev", page - 1 if page - 1 != 0 else 1),
                    self.btn("next", page + 1),
                    self.first_btn(),
                ]
            ).add_markups([2, 1])
