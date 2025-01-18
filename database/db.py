import asyncio
from datetime import datetime

import peewee
import peewee_async
from config import settings

database = peewee_async.PooledPostgresqlDatabase(
    database=settings.database,
    user=settings.db_user,
    host=settings.db_host,
    port=settings.db_port,
    password=settings.db_password
)


#     command_order = AutoField()  # Автоматический ID. Порядковый номер команды.
#     search_time = DateTimeField()  # Время запроса
#     user = ForeignKeyField(User, backref='commands_history')  # Привязка
#     command_name = TextField()  # Имя команды
#     product_name = TextField(null=True)  # Текст запроса (Название или код)
#     result_size = IntegerField(null=True)  # Количество предложенных товаров
#     price_range = TextField(null=True)  # Диапазон цен (команда custom)


class HistoryModel(peewee.Model):
    id = peewee.PrimaryKeyField(null=False)
    date = peewee.DateTimeField(default=datetime.now())
    user = peewee.ForeignKeyField("User", backref='history')
    command = peewee.CharField()

    class Meta:
        database = database


class ItemListModel(HistoryModel):
    search_name = peewee.CharField()
    result_qnt = peewee.IntegerField(null=True)
    price_range = peewee.TextField(null=True)

    class Meta:
        db_table = "history"
        order_by = "created_at"


class ItemDetailModel(HistoryModel):
    title = peewee.CharField(max_length=200)
    price = peewee.FloatField()
    reviews = peewee.IntegerField()
    stars = peewee.FloatField()
    image = peewee.CharField()
    class Meta:
        db_table = "history"
        order_by = "created_at"


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

# Look, sync code is working!

HistoryModel.create_table(True)
# HistoryModel.create(text="Yo, I can do it sync!")
database.close()

# Create async models manager:

objects = peewee_async.Manager(database)

# No need for sync anymore!

database.set_allow_sync(False)


async def handler():
    await objects.create(TestModel, text="Not bad. Watch this, I'm async!")
    all_objects = await objects.execute(TestModel.select())
    for obj in all_objects:
        print(obj.text)


loop = asyncio.get_event_loop()
loop.run_until_complete(handler())
loop.close()

# Clean up, can do it sync again:
with objects.allow_sync():
    TestModel.drop_table(True)

# Expected output:
# Yo, I can do it sync!
# Not bad. Watch this, I'm async!
