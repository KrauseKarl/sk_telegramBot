from datetime import datetime

import peewee
import peewee_async
from peewee import Model
from playhouse.migrate import PostgresqlMigrator, migrate
from pydantic import BaseModel

from core.config import *

db = peewee_async.PooledPostgresqlDatabase(
    database=conf.database,
    user=conf.db_user,
    host=conf.db_host,
    port=conf.db_port,
    password=conf.db_password
)
migrator = PostgresqlMigrator(db)


class Base(Model):
    date = peewee.DateTimeField(default=datetime.now())

    class Meta:
        database = db


class User(Base):
    """Таблица пользователей."""

    user_id = peewee.IntegerField(primary_key=True, unique=True)  # Первичный ключ Telegram ID
    user_name = peewee.TextField(null=True)  # Никнейм в telegram
    first_name = peewee.TextField(null=True)  # Имя в telegram
    last_name = peewee.TextField(null=True)  # Фамилия в telegram опционально.

    class Meta:
        db_table = "user"


class CacheData(Base):
    uid = peewee.PrimaryKeyField()
    key = peewee.CharField(unique=True)
    query = peewee.TextField()
    user = peewee.ForeignKeyField(
        User,
        backref='cache_data',
        to_field="user_id",
        related_name="cache_data"
    )


class History(Base):
    uid = peewee.PrimaryKeyField()
    command = peewee.CharField()

    search_name = peewee.CharField(null=True)
    result_qnt = peewee.IntegerField(null=True)
    price_range = peewee.TextField(null=True)
    price_min = peewee.TextField(null=True)
    price_max = peewee.TextField(null=True)
    sort = peewee.TextField(null=True)
    title = peewee.CharField(null=True, max_length=200)

    price = peewee.FloatField(null=True)
    reviews = peewee.IntegerField(null=True)
    stars = peewee.FloatField(null=True)
    url = peewee.CharField(null=True)
    image = peewee.CharField(null=True)
    user = peewee.ForeignKeyField(
        User,
        backref='history',
        to_field="user_id",
        related_name="history"
    )

    class Meta:
        db_table = "history"


class Favorite(Base):
    uid = peewee.PrimaryKeyField()
    product_id = peewee.CharField(max_length=200, unique=True)
    title = peewee.CharField(null=True, max_length=200)
    price = peewee.FloatField(null=True)
    reviews = peewee.IntegerField(null=True)
    stars = peewee.FloatField(null=True)
    url = peewee.CharField(null=True)
    image = peewee.CharField(null=True)
    user = peewee.ForeignKeyField(
        User,
        backref='favorite',
        to_field="user_id",
        related_name="favorite"
    )

    class Meta:
        db_table = "favorite"


#
# try:
#     image = peewee.CharField(null=True)
#     migrate(migrator.add_column('history', 'image', image), )
# except peewee.ProgrammingError:
#     pass


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