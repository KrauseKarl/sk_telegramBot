from database.models import *


# objects = peewee_async.Manager(database)
#
# with objects.allow_sync():
#     UserModel.create_table(True)
#     ItemListModel.create_table(True)
#     ItemDetailModel.create_table(True)

def create_tables():
    db.set_allow_sync(True)
    User.create_table(True)
    History.create_table(True)
    Favorite.create_table(True)
    CacheData.create_table(True)
    ItemSearch.create_table(True)
    DataEntry.create_table(True)
    db.close()

def drop_table():
    db.set_allow_sync(True)
    User.drop_table(True)
    History.drop_table(True)
    Favorite.drop_table(True)
    CacheData.drop_table(True)
    ItemSearch.drop_table(True)
    DataEntry.drop_table(True)
    db.close()

# def drop_table():
#     with objects.allow_sync():
#         User.drop_table(True)
#         Favorite.drop_table(True)
#         History.drop_table(True)
#         CacheData.drop_table(True)
#         ItemSearch.drop_table(True)
#         DataEntry.drop_table(True)


objects = peewee_async.register_database(db)

db.set_allow_sync(False)

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
