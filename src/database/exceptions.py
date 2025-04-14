from aiogram.exceptions import AiogramError
from httpx import HTTPError
from peewee import IntegrityError


class PeeweeError(IntegrityError):
    pass


class TelegramAPIError(AiogramError):
    pass


class FreeAPIExceededError(HTTPError):
    def __init__(self, message: str) -> None:
        self.message = message

    def __str__(self) -> str:
        return self.message

    def __repr__(self) -> str:
        return f"{type(self).__name__}('{self}')"


class CustomError(TelegramAPIError, PeeweeError):
    def __init__(self, message: str) -> None:
        self.message = message

    def __str__(self) -> str:
        return self.message

    def __repr__(self) -> str:
        return f"{type(self).__name__}('{self}')"
