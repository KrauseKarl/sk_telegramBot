from enum import Enum

from aiogram.filters import callback_data

from src.api_telegram.callback_data.base import Navigation


class FavoriteAction(str, Enum):
    list = "FAL"
    detail = "FAD"
    delete = "FDL"
    paginate = "FPG"


class FavoriteCBD(callback_data.CallbackData, prefix="FVT"):
    action: FavoriteAction
    navigate: Navigation
    page: int = 1
    item_id: str | int | None = None


class FavoriteAddDetailCBD(callback_data.CallbackData, prefix="FVT"):
    action: FavoriteAction
    item_id: str = None
    key: str
    api_page: int
    next: int
    prev: int
    first: int = 1
    last: int


class FavoriteAddCBD(FavoriteAddDetailCBD, prefix="FVT"):
    page: int


class FavoriteDeleteCBD(callback_data.CallbackData, prefix="FVT"):
    action: FavoriteAction
    navigate: Navigation
    page: int
    item_id: str | int | None = None
