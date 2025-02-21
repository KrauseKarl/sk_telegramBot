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


# class Action(str, Enum):
#     ban = "ban"
#     kick = "kick"
#     warn = "warn"
#
# class AdminAction(CallbackData, prefix="adm"):
#     action: Action
#     chat_id: int
#     user_id: int
#
# ...
# # Inside handler
# builder = InlineKeyboardBuilder()
# for action in Action:
#     builder.button(
#         text=action.value.title(),
#         callback_data=AdminAction(action=action, chat_id=chat_id, user_id=user_id),
#     )

class FavAction(str, Enum):
    list = "add_list"
    detail = "add_detail"
    page = "page"


class FavoriteCBD(CallbackData, prefix='favorite'):
    action: FavAction
    item_id: str
    page: str = None


builder = InlineKeyboardBuilder()

builder.button(
    text=FavAction.list.value.title(),
    callback_data=FavoriteCBD(action=FavAction.list, item_id="123"),
)
builder.button(
    text=FavAction.detail.value.title(),
    callback_data=FavoriteCBD(action=FavAction.detail, item_id="123"),
)
builder.button(
    text=FavAction.page.value.title(),
    callback_data=FavoriteCBD(action=FavAction.page, item_id="123", page='2'),
)
#   callback_data=AdminAction(action=FavAction., chat_id=chat_id, user_id=user_id),
#   callback_data=AdminAction(action=action, chat_id=chat_id, user_id=user_id),
#   callback_data=AdminAction(action=action, chat_id=chat_id, user_id=user_id),
