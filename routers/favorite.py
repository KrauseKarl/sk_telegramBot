from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from database.orm import *

favorite = Router()


@favorite.callback_query(F.data.startswith("favorite_add"))
async def make_favorite(callback: CallbackQuery, state: FSMContext) -> None:
    item_id = str(callback.data).split("_")[2]
    if item_id is not None:
        data = await state.get_data()
        data['user'] = callback.from_user.id
        print(data.items())
        await state.clear()
        item = await orm_get_or_create_favorite(data)
        await callback.answer('⭐️ {0:.10} \nдобавлен в избранное'.format(item.title))
