from enum import Enum

from aiogram.filters.callback_data import CallbackData

from api_telegram.callback_data import Navigation


# REVIEW ######################################################################################
class RevAction(str, Enum):
    first = "RFP"
    paginate = "RPG"


class ReviewAction(str, Enum):
    first = "RFP"
    paginate = "RPG"


class ReviewPageCBD(CallbackData, prefix='RVW'):
    action: RevAction
    navigate: Navigation
    page: int = 1


class ReviewCBD(CallbackData, prefix='RVW'):
    action: ReviewAction
    navigate: Navigation
    item_id: str | None = None
    key: str
    api_page: int | str
    page: str | int
    next: str | int
    prev: str | int
    first: str | int
    last: str | int
    sub_page: str | int
