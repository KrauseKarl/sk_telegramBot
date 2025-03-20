from enum import Enum

from aiogram.filters.callback_data import CallbackData

from api_telegram.callback_data import Navigation


# IMAGE ######################################################################################
class ImagesAction(str, Enum):
    images = "IFP"
    paginate = 'IPG'
    back = "IBD"


class ImageCBD(CallbackData, prefix='IMG'):
    action: ImagesAction
    navigate: Navigation
    item_id: str = None
    key: str
    api_page: int | str
    page: int | str
    next: int | str
    prev: int | str
    first: int | str
    last: int | str
    sub_page: str | int
