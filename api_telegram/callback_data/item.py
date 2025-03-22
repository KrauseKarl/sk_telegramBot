from enum import Enum

from aiogram.filters.callback_data import CallbackData


class ItemCBD(CallbackData, prefix='ITL'):
    key: str
    api_page: int
    page: int


class DetailAction(str, Enum):
    go_view = "gtDtl"
    back_list = "bcLst"
    back_detail = "bcDtl"


class DetailsAction(str, Enum):
    view = "DGD"
    list = "DBL"
    detail = "DBD"


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
