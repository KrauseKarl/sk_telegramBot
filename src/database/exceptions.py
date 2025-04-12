from aiogram.exceptions import AiogramError
from httpx import HTTPError
from peewee import IntegrityError


class PeeweeError(IntegrityError):
    pass


class TelegramAPIError(AiogramError):
    pass


class FreeAPIExceededError(HTTPError):
    pass


class CustomError(TelegramAPIError, PeeweeError):
    def __init__(self, message: str) -> None:
        self.message = message
