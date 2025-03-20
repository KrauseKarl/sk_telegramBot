# MONITOR ######################################################################################
from enum import Enum

from aiogram.filters.callback_data import CallbackData
from api_telegram.callback_data.base import Navigation


class MonitorAction(str, Enum):
    """

    """
    list = "LST"
    back = "BCK"
    graph = "GRAPH"
    add = "ADD"
    delete = "DEL"
    page = "PGN"


class MonitorCBD(CallbackData, prefix="Monitor"):
    """

    """
    action: MonitorAction
    navigate: Navigation | None = None
    item_id: str | int | None = None
    monitor_id: str | int | None = None
    page: int | int | None = None