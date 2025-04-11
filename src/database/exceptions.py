from aiogram.exceptions import AiogramError, TelegramBadRequest
from httpx import HTTPError
from peewee import IntegrityError


class PeeweeError(IntegrityError):
    pass


class TelegramAPIError(TelegramBadRequest, AiogramError):
    pass


class FreeAPIExceededError(HTTPError):
    pass


class CustomError(TelegramAPIError, PeeweeError):
    pass
