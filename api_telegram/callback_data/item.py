from enum import Enum

from aiogram.filters.callback_data import CallbackData


class ItemCBD(CallbackData, prefix='ITL'):
    key: str
    api_page: int
    page: int


class DetailAction(str, Enum):
    go_view = "DGD"
    back_list = "DBL"
    back_detail = "DBD"


class DetailCBD(CallbackData, prefix='ITD'):
    action: DetailAction
    item_id: str = None
    key: str
    api_page: int
    page: int
    next: int
    prev: int
    first: int = 1
    last: int
