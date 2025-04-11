from aiogram.filters.callback_data import CallbackData


class CacheKey(CallbackData, prefix="redis"):
    # user_id: int | None = None
    key: str
    extra: str | None = None
    api_page: str | int


class CacheKeyExtended(CallbackData, prefix="redis"):
    # user_id: int | None = None
    key: str
    extra: str | None = None
    api_page: str | int
    sub_page: str | int


class CacheKeyReview(CallbackData, prefix="redis"):
    # user_id: int | None = None
    key: str
    api_page: int
    extra: str | None = None
    page: int
    review: str = "review"
