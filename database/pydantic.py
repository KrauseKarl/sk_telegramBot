from pydantic import BaseModel


class HistoryModel(BaseModel):
    command: str
    user: int
    search_name: str | None = None
    result_qnt: int | None = None
    price_range: str | None = None
    price_min: str | int | None = None
    price_max: str | int | None = None
    title: str | None = None
    price: float | None = None
    reviews: int | None = None
    stars: float | None = None
    url: str | None = None
    image: str | None = None
    sort: str | None = None


class FavoriteModel(BaseModel):
    title: str = None
    price: float = None
    reviews: int = None
    stars: float = None
    url: str = None
    image: str = None
    user: int = None


class CacheDataModel(BaseModel):
    key: str
    query: str
    user: int


class CacheDataUpdateModel(BaseModel):
    query: str
