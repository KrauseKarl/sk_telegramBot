# FAVORITE ######################################################################################
from enum import Enum

from aiogram.filters.callback_data import CallbackData

from api_telegram.callback_data.base import Navigation


class FavoriteAction(str, Enum):
    list = "FAL"
    detail = "FAD"
    delete = "FDL"
    page = "FPG"


class FavoriteCBD(CallbackData, prefix='FVT'):
    action: FavoriteAction
    navigate: Navigation
    page: int = 1


class FavoriteAddDetailCBD(CallbackData, prefix='FVT'):
    action: FavoriteAction
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
    action: FavoriteAction
    item_id: str | int
    page: int
