import math
from typing import List

from api_telegram.callback_data import *
from database.models import *
from utils.message_info import *


# PAGINATOR CLASS ###############################################################
class Paginator:
    def __init__(self, array: list | tuple, page: int = 1, per_page: int = 1):
        self.array = array
        self.per_page = per_page
        self.page = page
        self.len = len(self.array)
        self.pages = math.ceil(self.len / self.per_page)
        self.total_pages = (len(self.array) + self.per_page - 1) // self.per_page

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

    # def delete_item(self, item):
    #     if item in self.array:
    #         self.array.remove(item)
    #         self.total_pages = (len(self.array) + self.per_page - 1) // self.per_page
    #         if self.page > self.total_pages:
    #             self.page = self.total_pages
    #         print(f"Item '{item}' deleted.")
    #     else:
    #         print(f"Item '{item}' not found.")

    # def get_current_page_items(self):
    #     start_index = (self.current_page - 1) * self.items_per_page
    #     end_index = start_index + self.items_per_page
    #     return self.data[start_index:end_index]
    def __get_slice(self):
        start = (self.page - 1) * self.per_page
        stop = start + self.per_page
        # print(f"_____________Ⓜ️💛 get_slice | [start] {start} <-> {stop}  [end] ")
        return self.array[start:stop]

    def ___get_back_item(self):
        start = (self.page - 2) * self.per_page
        stop = start + self.per_page
        # print(f"_____________Ⓜ️❤️ get_back_item | [start] {start} <-> {stop}  [end] ")
        return self.array[start:stop]

    def ___get_next_item(self):
        start = (self.page + 1) * self.per_page
        stop = start + self.per_page
        # print(f"_____________️Ⓜ️💚  get_next_item | [start] {start} <-> {stop}  [end] ")
        return self.array[start:stop]

    def delete(self, delete_page):
        result = None
        if self.total_pages == 1:
            # [1] - > [x] -> None
            if delete_page == 1:

                result = None
                print(f"_____________1️⃣Ⓜ️ {result = }")

        if 1 < self.total_pages < 3:
            if delete_page == 1:
                # [1][2] - > [x][2] -> [2->1] - > [1]

                result = self.___get_next_item()
                print(f"_____________2️⃣Ⓜ️ {result = }")
            else:

                result = self.__get_slice()
                print(f"#3️⃣Ⓜ️")
                # [1][2] - > [1][x] -> [1]
        if 3 < self.total_pages:
            if delete_page == 1:

                # [1][2][3] - > [x][2][3] -> [2->1][3->2] - > [1][2]
                result = self.___get_next_item()
                print(f"_____________4️⃣Ⓜ️ {result = }")
            else:

                # [1][2][3] - > [1][2][x] -> [1][2]
                # [1][2][3] - > [1][x][3] -> [1][3->2] - > [1][2]
                result = self.___get_back_item()
                print(f"_____________5️⃣Ⓜ️ {result = }")

        return result

    def display_page(self):
        return "{0} из {1}".format(self.page, self.total_pages)


# PAGINATOR BUTTONS FUNC #############################################################
def pages(paginator: Paginator):
    buttons = dict()

    if paginator.has_previous():
        buttons["◀ пред."] = "previous"
    if paginator.has_next():
        buttons["след. ▶"] = "next"

    return buttons
