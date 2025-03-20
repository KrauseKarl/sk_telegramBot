from aiogram.filters.callback_data import CallbackData


class CacheKey(CallbackData, prefix='redis'):
    # user_id: int | None = None
    key: str
    api_page: str | int
    extra: str | None = None


class CacheKeyExtended(CallbackData, prefix='redis'):
    # user_id: int | None = None
    key: str
    api_page: str | int
    extra: str | None = None
    sub_page: str | int
