from enum import Enum

from aiogram.filters.callback_data import CallbackData

from api_telegram.callback_data import Navigation


# IMAGE ######################################################################################
class ImagesAction(str, Enum):
    images = "IFP"
    paginate = 'IPG'
    back = "IBD"


class ImagePageCBD(CallbackData, prefix='IMG'):
    action: ImagesAction
    navigate: Navigation
    page: int = 1


class ImageCBD(CallbackData, prefix='IMG'):
    action: ImagesAction
    navigate: Navigation
    item_id: str = None
    key: str
    api_page: int
    page: int
    next: int
    prev: int
    first: int = 1
    last: int
    sub_page: int
