from enum import Enum

from aiogram.filters.callback_data import CallbackData
from api_telegram.callback_data.base import Navigation


class JobCBD(CallbackData, prefix="Job"):
    uid: int


class MonitorAction(str, Enum):
    """

    """
    list = "LST"
    back = "BCK"
    graph = "GRAPH"
    add = "ADD"
    delete = "DEL"
    paginate = "PGN"
    target = "TGT"


class MonitorCBD(CallbackData, prefix="Monitor"):
    """

    """
    action: MonitorAction
    navigate: Navigation | None = None
    key: str | None = None
    item_id: str | None = None
    monitor_id: int | None = None
    page: int | None = None
