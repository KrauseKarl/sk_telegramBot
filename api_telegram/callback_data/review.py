from enum import Enum

from aiogram.filters.callback_data import CallbackData

from api_telegram.callback_data import Navigation


# REVIEW ######################################################################################
class ReviewAction(str, Enum):
    first = "RFP"
    paginate = "RPG"


class ReviewPageCBD(CallbackData, prefix='RVW'):
    action: ReviewAction
    navigate: Navigation
    page: int = 1


class ReviewCBD(CallbackData, prefix='RVW'):
    action: ReviewAction
    navigate: Navigation
    item_id: str | None = None
    key: str
    api_page: int
    page: int
    next: int
    prev: int
    first: int = 1
    last: int
    sub_page: int
