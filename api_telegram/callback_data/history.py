from enum import Enum

from aiogram.filters.callback_data import CallbackData

from api_telegram.callback_data import Navigation


class HistoryAction(str, Enum):
    first = "RFP"
    paginate = "RPG"


class HistoryCBD(CallbackData, prefix='HST'):
    action: HistoryAction
    navigate: Navigation
    page: int = 1
