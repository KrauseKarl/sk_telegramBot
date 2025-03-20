from enum import Enum

from aiogram.filters.callback_data import CallbackData
from aiogram.utils.keyboard import InlineKeyboardBuilder


class BasePagination(str, Enum):
    next = "nxt"
    prev = "prv"
    last = "lts"
    first = "fst"


class Navigation(str, Enum):
    next = "NXT"
    prev = "PRV"
    last = "LST"
    first = "FRT"


class CacheKey(CallbackData, prefix='redis'):
    # user_id: int | None = None
    key: str
    api_page: str | int
    extra: str | None = None


class CacheKeyExtended(CallbackData, prefix='redis'):
    # user_id: int | None = None
    key: str
    api_page: str | int
    extra: str | None = None
    sub_page: str | int


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


# FAVORITE ######################################################################################
class FavAction(str, Enum):
    list = "add_lst"
    detail = "add_dtl"
    delete = "del"
    page = "page"


class FavoriteAction(str, Enum):
    add_list = "FAL"
    aad_detail = "FAD"
    delete = "FDL"
    paginate = "FPG"


class FavPagination(str, Enum):
    next = "nxt"
    prev = "prv"
    last = "lts"
    first = "fst"


class FavoritePageCBD(CallbackData, prefix='FVT'):
    action: FavAction
    navigate: FavPagination
    page: int = 1


class FavoriteAddDetailCBD(CallbackData, prefix='FVT'):
    action: FavAction
    item_id: str = None
    key: str
    api_page: str
    next: str
    prev: str
    first: str
    last: str


class FavoriteAddCBD(FavoriteAddDetailCBD, prefix='FVT'):
    page: str


class FavoriteDeleteCBD(CallbackData, prefix='FVT'):
    action: FavAction
    item_id: str
    page: int


# REVIEW ######################################################################################
class RevAction(str, Enum):
    first = "first"
    page = "page"


class ReviewAction(str, Enum):
    first = "RFP"
    paginate = "RPG"


class RevNavigate(str, Enum):
    next = "nxt"
    prev = "prv"
    last = "lts"
    first = "fst"


class ReviewPageCBD(CallbackData, prefix='RVW'):
    action: RevAction
    navigate: RevNavigate
    page: int = 1


class ReviewCBD(CallbackData, prefix='RVW'):
    action: RevAction
    navigate: RevNavigate
    item_id: str | None = None
    key: str
    api_page: int | str
    page: str | int
    next: str | int
    prev: str | int
    first: str | int
    last: str | int
    review_page: str | int


# IMAGE ######################################################################################
class ImgAction(str, Enum):
    images = "img"
    page = 'pgn'
    back = "bck"


class ImgNavigation(str, Enum):
    next = "nx"
    prev = "pr"
    last = "lt"
    first = "ft"


class ImagesAction(str, Enum):
    images = "IFP"
    paginate = 'IPG'
    back = "IBD"


class ImageCBD(CallbackData, prefix='IMG'):
    action: ImgAction
    navigate: ImgNavigation
    item_id: str = None
    key: str
    api_page: int | str
    page: int | str
    next: int | str
    prev: int | str
    first: int | str
    last: int | str
    img_page: str | int


# BASE ######################################################################################
class BaseCBD(CallbackData, prefix='BS'):
    action: DetailAction | FavoriteAction | ReviewAction | ImgAction
    navigate: Navigation
    item_id: str | int | None = None
    key: str
    api_page: str | int
    next: str | int
    prev: str | int
    first: str | int
    last: str | int
    extra_page: str | int | None = None


# MONITOR ######################################################################################
class MonitorAction(str, Enum):
    list = "LST"
    back = "BCK"
    graph = "GRAPH"
    add = "ADD"
    delete = "DEL"
    page = "PGN"


class MonitorCBD(CallbackData, prefix="Monitor"):
    action: MonitorAction
    navigate: Navigation | None = None
    item_id: str | int | None = None
    monitor_id: str | int | None = None
    page: int | int | None = None
