from enum import Enum

from aiogram.filters.callback_data import CallbackData
from aiogram.utils.keyboard import InlineKeyboardBuilder


class CacheKey(CallbackData, prefix='redis'):
    key: str
    api_page: str
    # paginate_page: str


class ItemCBD(CallbackData, prefix='itList'):
    key: str
    api_page: int | str
    paginate_page: int | str


class DetailCBD(CallbackData, prefix='itDetail'):
    item_id: str


class FavAction(str, Enum):
    list = "add_from_list"
    detail = "add_from_detail"
    delete = "delete_from_favorites"
    page = "page"


class FavoriteAddCBD(CallbackData, prefix='favorite'):
    action: FavAction
    item_id: str = None
    key: str
    api_page: str
    next: str
    prev: str
    first: str
    last: str


class FavoriteDeleteCBD(CallbackData, prefix='favorite'):
    action: FavAction
    item_id: str
    page: str


class FavPagination(str, Enum):
    next = "next_page"
    prev = "prev_page"
    last = "lats_page"
    first = "first_page"


class FavoritePageCBD(CallbackData, prefix='favorite'):
    action: FavAction
    page: FavPagination
    pages: int = 1
