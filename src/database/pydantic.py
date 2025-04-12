from pydantic import BaseModel


class HistoryModel(BaseModel):
    user: int
    product_id: str
    title: str
    price: float
    reviews: int
    stars: float
    url: str
    image: str


class FavoriteModel(BaseModel):
    title: str | None = None
    price: float | None = None
    reviews: int | None = None
    stars: float | None = None
    url: str | None = None
    image: str | None = None
    user: int | None = None


class CacheDataModel(BaseModel):
    key: str
    query: str
    user: int


class CacheDataUpdateModel(BaseModel):
    query: str
