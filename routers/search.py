from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from database.exceptions import *
from keyboards import *
from request import *
from statments import *
from utils import *

search = Router()


# ITEM LIST ############################################################################################################
@search.message(Command("search"))
async def search_name_message(message: Message, state: FSMContext) -> None:
    try:
        await state.set_state(Form.product)
        await message.edit_media(
            media=await get_input_media_hero_image(
                "search",
                "🛍️ Введите название товара.")
        )
    except TelegramBadRequest:
        await state.set_state(Form.product)
        await message.answer_photo(
            photo=await get_fs_input_hero_image("search", ),
            caption="🛍️ Введите название товара."
        )
    except CustomError as error:
        await message.edit_media(
            media=await get_error_answer_media(error),
            reply_markup=menu_kb
        )


@search.callback_query(F.data.startswith("search"))
async def search_name_callback(callback: CallbackQuery, state: FSMContext) -> None:
    try:
        await state.set_state(Form.product)
        await callback.message.edit_media(
            media=await get_input_media_hero_image(
                "search",
                "🛍️ Введите название товара.")
        )
    except CustomError as error:
        await callback.message.edit_media(
            media=await get_error_answer_media(error),
            reply_markup=menu_kb
        )


@search.message(Form.product)
async def search_sort(message: Message, state: FSMContext) -> None:
    try:
        await state.update_data(product=message.text)
        await state.set_state(Form.sort)
        await message.answer_photo(
            photo=await get_fs_input_hero_image("sort"),
            caption="Как отсортировать результат?",
            reply_markup=sort_kb
        )
    except CustomError as error:
        msg, photo = await get_error_answer_photo(error)
        await message.answer_photo(
            photo=photo,
            caption=msg,
            reply_markup=menu_kb
        )


@search.callback_query(Form.sort, F.data.in_(SORT_SET))
async def search_qnt(callback: CallbackQuery, state: FSMContext) -> None:
    try:
        await state.update_data(sort=callback.data)
        await state.set_state(Form.qnt)
        await callback.message.edit_media(
            media=await get_input_media_hero_image(
                "quantity",
                "сколько единиц товара вывести?"),
            reply_markup=await get_qnt_kb()
        )
    except CustomError as error:
        await callback.message.edit_media(
            media=await get_error_answer_media(error),
            reply_markup=menu_kb
        )


@search.callback_query(Form.qnt, F.data.in_(QNT))
async def search_result(call: CallbackQuery, state: FSMContext) -> None:
    # try:
        await state.update_data(qnt=call.data)
        data = await state.get_data()
        await call.answer("⌛ searching {0}".format(data['product']))

        result = await request_item_list(
            q=data.get("product"),
            sort=data.get("sort"),
            url="item_search_2"
        )
        # todo fix bug with status
        # if result['status']["code"] != 200:
        #     raise FreeAPIExceededError(
        #         message="❌ лимит API превышен\n{0}".format(
        #             result.get('message')
        #         )
        #     )

        item_list = await deserialize_item_list(
            response=result,
            user_id=call.from_user.id,
            data=data
        )
        for msg, img, kb in item_list:
            await call.message.answer(msg, reply_markup=kb)

        await state.clear()
    #
    # except FreeAPIExceededError as error:
    #     await call.message.answer("⚠️ Ошибка\n{0}".format(str(error)))
    # except CustomError as error:
    #     msg, photo = await get_error_answer_photo(error)
    #     await call.message.answer_photo(photo=photo, caption=msg)
