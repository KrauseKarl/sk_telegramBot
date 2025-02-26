from enum import Enum

from aiogram.filters.callback_data import CallbackData
from aiogram.utils.keyboard import InlineKeyboardBuilder


class CacheKey(CallbackData, prefix='redis'):
    key: str
    api_page: str | int


class ItemCBD(CallbackData, prefix='itList'):
    key: str
    api_page: int | str
    page: int | str


class DetailAction(str, Enum):
    view = "view"
    back = "back"


class DetailCBD(CallbackData, prefix='itDetail'):
    action: DetailAction
    item_id: str = None
    key: str
    api_page: int | str
    page: str
    next: str
    prev: str
    first: str
    last: str


class FavAction(str, Enum):
    list = "add_list"
    detail = "add_detail"
    delete = "delete"
    page = "page"


class FavPagination(str, Enum):
    next = "next_page"
    prev = "prev_page"
    last = "lats_page"
    first = "first_page"


class FavoritePageCBD(CallbackData, prefix='favorite'):
    action: FavAction
    navigate: FavPagination
    page: int = 1


# class FavoriteAddCBD(CallbackData, prefix='favorite'):
#     action: FavAction
#     item_id: str = None
#     key: str
#     api_page: str
#     next: str
#     prev: str
#     first: str
#     last: str
#
#     page: str


class FavoriteAddDetailCBD(CallbackData, prefix='favorite'):
    action: FavAction
    item_id: str = None
    key: str
    api_page: str
    next: str
    prev: str
    first: str
    last: str


class FavoriteAddCBD(FavoriteAddDetailCBD, prefix='favorite'):
    page: str


class FavoriteDeleteCBD(CallbackData, prefix='favorite'):
    action: FavAction
    item_id: str
    page: str
