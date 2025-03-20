from pydantic import BaseModel


class HistoryModel(BaseModel):

    user: int
    product_id: str | int
    title: str
    price: float | int
    reviews: int
    stars: float | int
    url: str
    image: str


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
