from aiogram.exceptions import AiogramError
from httpx import HTTPError
from peewee import IntegrityError


class CustomError(AiogramError, IntegrityError):
    pass


class FreeAPIExceededError(HTTPError):
    pass
