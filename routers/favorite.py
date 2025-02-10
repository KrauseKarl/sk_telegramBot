from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from peewee import IntegrityError

from database.orm import *
from keyboards import *
favorite = Router()


@favorite.callback_query(F.data.startswith("favorite_add"))
async def make_favorite(callback: CallbackQuery, state: FSMContext) -> None:
    item_id = str(callback.data).split("_")[2]
    img_qnt = str(callback.data).split("_")[-1]
    try:
        if item_id is not None:
            data = await state.get_data()
            data['user'] = callback.from_user.id
            item, created = await orm_get_or_create_favorite(data)
            print(f"make_favorite = {item} | {created}")
            await callback.answer('⭐️ добавлен в избранное')
            kb = await kb_builder(
                size=(2,),
                data_list=[
                    {"свернуть": "delete_{0}_{1}".format(item_id, img_qnt)},
                    {"отслеживать цену": "price"}
                ]
            )
            await callback.message.edit_reply_markup(reply_markup=kb)
    except IntegrityError:
        await callback.answer("‼️️ уже добавлено в избранное")