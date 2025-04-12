import math
from typing import Any, Union


class Paginator:
    """Класс для создания пагинации."""

    def __init__(self, array: Union[list, tuple], page: int = 1, per_page: int = 1):
        self.array = array
        self.per_page = per_page
        self.page = page
        self.len = len(self.array)
        self.pages = math.ceil(self.len / self.per_page)
        self.total_pages = (len(self.array) + self.per_page - 1) // self.per_page

    def get_page(self) -> Any:
        page_items = self.__get_slice()
        return page_items

    def has_next(self) -> Union[int, bool]:
        if self.page < self.pages:
            return self.page + 1
        return False

    def has_previous(self) -> Union[int, bool]:
        if self.page > 1:
            return self.page - 1
        return False

    def get_next(self) -> Any:
        if self.page < self.pages:
            self.page += 1
            return self.get_page()
        raise IndexError("Следующей страницы не существует.")

    def get_previous(self) -> Any:
        if self.page > 1:
            self.page -= 1
            return self.__get_slice()
        raise IndexError("Предыдущая страница не существует.")

    def __get_slice(self) -> Any:
        start = (self.page - 1) * self.per_page
        stop = start + self.per_page
        return self.array[start:stop]

    def ___get_back_item(self) -> Any:
        start = (self.page - 2) * self.per_page
        stop = start + self.per_page
        return self.array[start:stop]

    def ___get_next_item(self) -> Any:
        start = (self.page + 1) * self.per_page
        stop = start + self.per_page
        return self.array[start:stop]

    def delete(self, delete_page) -> Any:
        result = None
        if self.total_pages == 1:
            if delete_page == 1:
                result = None
        if 1 < self.total_pages < 3:
            if delete_page == 1:
                result = self.___get_next_item()
            else:
                result = self.__get_slice()
        if 3 < self.total_pages:
            if delete_page == 1:
                result = self.___get_next_item()
            else:
                result = self.___get_back_item()
        return result

    def display_page(self) -> str:
        """Возвращает строку с текущей страницей и общим кол-вом страниц"""
        return "{0} из {1}".format(self.page, self.total_pages)


class PaginatorHandler:
    """Класс для работы с пагинацией"""

    def __init__(self, array: list, page: int):
        self.array = array
        self.page = page

    async def get_paginator(self) -> Paginator:
        """Создает пагинацию."""
        return Paginator(array=self.array, page=self.page)

    @property
    async def get_item(self):
        """Возвращает один элемент списка."""
        paginator = await self.get_paginator()
        return paginator.get_page()[0]

    @property
    async def get_paginator_len(self) -> int:
        """Возвращает длину списка."""
        paginator = await self.get_paginator()
        return paginator.len
