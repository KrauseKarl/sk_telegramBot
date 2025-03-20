from enum import Enum

from aiogram.filters.callback_data import CallbackData


class ItemCBD(CallbackData, prefix='ITL'):
    key: str
    api_page: int | str
    page: int | str


class DetailAction(str, Enum):
    go_view = "gtDtl"
    back_list = "bcLst"
    back_detail = "bcDtl"


class DetailCBD(CallbackData, prefix='ITD'):
    action: DetailAction
    item_id: str = None
    key: str
    api_page: int | str
    page: int | str
    next: int | str
    prev: int | str
    first: int | str
    last: int | str


class DetailsAction(str, Enum):
    view = "DGD"
    list = "DBL"
    detail = "DBD"
