import math
from typing import List

from api_telegram.keyboards import *
from database.models import *
from utils.message_info import *
from utils.message_info import favorite_info, history_info


# PAGINATOR CLASS ###############################################################
class Paginator:
    def __init__(self, array: list | tuple, page: int = 1, per_page: int = 1):
        self.array = array
        self.per_page = per_page
        self.page = page
        self.len = len(self.array)
        self.pages = math.ceil(self.len / self.per_page)

    def __get_slice(self):
        start = (self.page - 1) * self.per_page
        stop = start + self.per_page
        return self.array[start:stop]

    def get_page(self):
        page_items = self.__get_slice()
        return page_items

    def has_next(self):
        if self.page < self.pages:
            return self.page + 1
        return False

    def has_previous(self):
        if self.page > 1:
            return self.page - 1
        return False

    def get_next(self):
        if self.page < self.pages:
            self.page += 1
            return self.get_page()
        raise IndexError(f'Next page does not exist.')

    def get_previous(self):
        if self.page > 1:
            self.page -= 1
            return self.__get_slice()
        raise IndexError(f'Previous page does not exist.')


# PAGINATOR BUTTONS FUNC #############################################################
def pages(paginator: Paginator):
    buttons = dict()

    if paginator.has_previous():
        buttons["◀ пред."] = "previous"
    if paginator.has_next():
        buttons["след. ▶"] = "next"

    return buttons


# HISTORY LIST PAGINATOR  ##############################################################
async def make_paginate_history_list(
        history_list: List[History], page: int = 1
):
    if len(history_list) == 0:
        msg = "⭕️у вас нет истории просмотров"
        kb = await kb_builder(
            size=(1,),
            data_list=[
                {"🏠 назад": "menu"}
            ]
        )
        return msg, kb, None

    kb = await kb_builder(
        size=(1,),
        data_list=[
            {"След. ▶": "page_fav_next_{0}".format(int(page) + 1)},
            {"🏠 меню": "menu"},
        ]
    )

    paginator = Paginator(history_list, page=page)
    one_items = paginator.get_page()[0]
    msg = await history_info(one_items)
    msg = msg + "\n{0} из {1}".format(page, paginator.pages)

    return msg, kb, one_items.image


# FAVORITES LIST PAGINATOR  ##############################################################
async def make_paginate_favorite_list(
        favorite_list: List[Favorite], page: int = 1
):
    if len(favorite_list) == 0:
        msg = "⭕️ у вас пока нет избранных товаров"
        kb = await kb_builder(
            size=(1,),
            data_list=[
                {"🏠 назад": "menu"}
            ]
        )
        return msg, kb, None
    else:
        paginator = Paginator(favorite_list, page=page)
        one_items = paginator.get_page()[0]
        print(one_items)
        msg = await favorite_info(one_items)
        msg = msg + "\n{0} из {1}".format(page, paginator.pages)
        if len(favorite_list) == 1:
            kb = await kb_builder(
                size=(1,),
                data_list=[
                    {"🏠 назад": "menu"}
                ]
            )
        else:
            kb = await kb_builder(
                size=(1,),
                data_list=[
                    {"След. ▶": "fav_page_next_{0}".format(int(page) + 1)},
                    {"🏠 меню": "menu"},
                ]
            )
        return msg, kb, one_items.image



