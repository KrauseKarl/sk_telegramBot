from datetime import datetime

import peewee
import peewee_async
from playhouse.migrate import PostgresqlMigrator, migrate

from config import conf

db = peewee_async.PooledPostgresqlDatabase(
    database=conf.database,
    user=conf.db_user,
    host=conf.db_host,
    port=conf.db_port,
    password=conf.db_password
)
migrator = PostgresqlMigrator(db)


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


class History(BaseModel):
    uid = peewee.PrimaryKeyField()
    date = peewee.DateTimeField(default=datetime.now())
    command = peewee.CharField()

    search_name = peewee.CharField(null=True)
    result_qnt = peewee.IntegerField(null=True)
    price_range = peewee.TextField(null=True)
    title = peewee.CharField(null=True, max_length=200)

    price = peewee.FloatField(null=True)
    reviews = peewee.IntegerField(null=True)
    stars = peewee.FloatField(null=True)
    url = peewee.CharField(null=True)
    image = peewee.CharField(null=True)
    user = peewee.ForeignKeyField(
        UserModel,
        backref='history',
        to_field="user_id",
        related_name="history"
    )

    class Meta:
        db_table = "history"


try:
    image = peewee.CharField(null=True)
    migrate(migrator.add_column('history', 'image', image), )
except peewee.ProgrammingError:
    pass
