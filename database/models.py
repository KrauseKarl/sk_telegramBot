from datetime import datetime

import peewee
import peewee_async

from config import settings

db = peewee_async.PooledPostgresqlDatabase(
    database=settings.database,
    user=settings.db_user,
    host=settings.db_host,
    port=settings.db_port,
    password=settings.db_password
)


class BaseModel(peewee.Model):

    class Meta:
        database = db


class UserModel(BaseModel):
    """Таблица пользователей."""

    # id = peewee.PrimaryKeyField(primary_key=True, null=False)
    # uid = peewee.PrimaryKeyField()
    user_id = peewee.IntegerField(primary_key=True, null=False)  # Первичный ключ Telegram ID
    user_name = peewee.TextField(null=True)  # Никнейм в telegram
    first_name = peewee.TextField(null=True)  # Имя в telegram
    last_name = peewee.TextField(null=True)  # Фамилия в telegram опционально.

    class Meta:
        db_table = "user"


class ItemListModel(BaseModel):
    # id = peewee.PrimaryKeyField(primary_key=True, null=False)
    uid = peewee.PrimaryKeyField()
    date = peewee.DateTimeField(default=datetime.now())
    command = peewee.CharField()
    search_name = peewee.CharField(null=True)
    result_qnt = peewee.IntegerField(null=True)
    price_range = peewee.TextField(null=True)
    user = peewee.ForeignKeyField(UserModel, backref='item_list', to_field="user_id", related_name="items")

    class Meta:
        db_table = "item_list"


class ItemDetailModel(BaseModel):
    uid = peewee.PrimaryKeyField()
    # id = peewee.PrimaryKeyField(primary_key=True,  null=False)
    date = peewee.DateTimeField(default=datetime.now())
    command = peewee.CharField()
    title = peewee.CharField(max_length=200, null=True)
    price = peewee.FloatField(null=True)
    reviews = peewee.IntegerField(null=True)
    stars = peewee.FloatField(null=True)
    image = peewee.CharField(null=True)
    user = peewee.ForeignKeyField(UserModel, backref='item_detail', to_field="user_id", related_name="item")

    class Meta:
        db_table = "item_detail"

#     command_order = AutoField()  # Автоматический ID. Порядковый номер команды.
#     search_time = DateTimeField()  # Время запроса
#     user = ForeignKeyField(User, backref='commands_history')  # Привязка
#     command_name = TextField()  # Имя команды
#     product_name = TextField(null=True)  # Текст запроса (Название или код)
#     result_size = IntegerField(null=True)  # Количество предложенных товаров
#     price_range = TextField(null=True)  # Диапазон цен (команда custom)

# class User(BaseModel):
#     """Таблица пользователей."""
#
#     user_id = IntegerField(primary_key=True)  # Первичный ключ Telegram ID
#     user_name = TextField(null=True)  # Никнейм в telegram
#     first_name = TextField()  # Имя в telegram
#     last_name = TextField(null=True)  # Фамилия в telegram опционально.
#
#
# class History(BaseModel):
#     """Таблица истории команд."""
#

#
#     def __str__(self):
#         """Строковое представление записи истории команд."""
#         return (
#             '{num} - {dtime}, /{comm}, a-{name}, b-{limit}, c-{range}'
#         ).format(
#             num=self.command_order,
#             dtime=self.search_time.strftime(DATETIME_FORMAT),
#             comm=self.command_name,
#             name=self.product_name,
#             limit=self.result_size,
#             range=self.price_range,
#         )
