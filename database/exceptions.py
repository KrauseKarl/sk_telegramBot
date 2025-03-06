from aiogram.exceptions import AiogramError, TelegramBadRequest
from httpx import HTTPError, ReadTimeout
from peewee import IntegrityError


class DBError(IntegrityError):
    pass


class CustomError(AiogramError, DBError):
    pass


class FreeAPIExceededError(HTTPError):
    pass
