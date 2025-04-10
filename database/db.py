import peewee_async

from database import models as m


def create_tables():
    """Создает таблицы в БД."""

    m.db.set_allow_sync(True)
    m.User.create_table(True)
    m.History.create_table(True)
    m.Favorite.create_table(True)
    m.CacheData.create_table(True)
    m.ItemSearch.create_table(True)
    m.DataEntry.create_table(True)
    m.db.close()


def drop_table():
    """Удаляет таблицы в БД."""
    m.db.set_allow_sync(True)
    m.User.drop_table(True)
    m.History.drop_table(True)
    m.Favorite.drop_table(True)
    m.CacheData.drop_table(True)
    m.ItemSearch.drop_table(True)
    m.DataEntry.drop_table(True)
    m.db.close()


objects = peewee_async.register_database(m.db)

m.db.set_allow_sync(False)

# async def handler():
#     await objects.create(TestModel, text="Not bad. Watch this, I'm async!")
#     all_objects = await objects.execute(TestModel.select())
#     for obj in all_objects:
#         print(obj.text)

# def _event_loop(request: Request) -> AbstractEventLoop:
#     loop = asyncio.get_event_loop_policy().new_event_loop()
#     yield loop
#     loop.close()


# async with asyncio.get_event_loop() as loop:
#     loop.run_until_complete()

# Clean up, can do it sync again:

# with objects.allow_sync():
#     TestModel.drop_table(True)
