from database.models import *

# Look, sync code is working!

# objects = peewee_async.Manager(database)
#
# with objects.allow_sync():
#     UserModel.create_table(True)
#     ItemListModel.create_table(True)
#     ItemDetailModel.create_table(True)
def create_tables():
    # MODELS = [UserModel, ItemDetailModel, ItemListModel]
    db.set_allow_sync(True)
    # db.create_tables([MODELS], safe=True)
    UserModel.create_table(True)
    # ItemDetailModel.create_table(True)
    History.create_table(True)
    # ItemListModel.create_table(True)
    db.close()
    # # with db.connect() as database:
    # db.set_allow_sync(True)
    # # db.connect()
    # db.create_tables(UserModel)
    # db.close()
    # # database.create_tables(ItemListModel)
    # # database.create_tables(ItemDetailModel)


def drop_table():
    with objects.allow_sync():
        UserModel.drop_table(True)
        # ItemDetailModel.drop_table(True)
        History.drop_table(True)
        # ItemListModel.drop_table(True)


# Create async models manager:
objects = peewee_async.register_database(db)

# No need for sync anymore!
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
