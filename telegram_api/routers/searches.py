import asyncio

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from data_api.deserializers import *
from data_api.request import *
from database.exceptions import *
from telegram_api.statments import *
from utils.media import *

search = Router()


# ITEM LIST ############################################################################################################
@search.message(Command("search"))
async def search_name_message(message: Message, state: FSMContext) -> None:
    """
    
    :param message: 
    :param state: 
    :return: 
    """
    try:
        await state.set_state(ItemFSM.product)
        await message.edit_media(
            media=await get_input_media_hero_image(
                "search",
                "🛍️ Введите название товара.")
        )
    except TelegramBadRequest:
        await state.set_state(ItemFSM.product)
        await message.answer_photo(
            photo=await get_fs_input_hero_image("search", ),
            caption="🛍️ Введите название товара."
        )
    except CustomError as error:
        await message.edit_media(
            media=await get_error_answer_media(error),
            reply_markup=await menu_kb()
        )


@search.callback_query(F.data.startswith("search"))
async def search_name_callback(callback: CallbackQuery, state: FSMContext) -> None:
    """
    
    :param callback: 
    :param state: 
    :return: 
    """
    try:
        await state.set_state(ItemFSM.product)
        await callback.message.edit_media(
            media=await get_input_media_hero_image(
                "search",
                "🛍️ Введите название товара.")
        )
    except CustomError as error:
        await callback.message.edit_media(
            media=await get_error_answer_media(error),
            reply_markup=await menu_kb()
        )


@search.message(ItemFSM.product)
async def search_sort(message: Message, state: FSMContext) -> None:
    """
    
    :param message: 
    :param state: 
    :return: 
    """
    try:
        await message.bot.delete_message(
            chat_id=message.chat.id,
            message_id=message.message_id
        )

        await state.update_data(product=message.text)
        await state.set_state(ItemFSM.sort)
        message_ = (int(message.message_id) - 1)
        
        await message.bot.edit_message_media(
            chat_id=message.chat.id,
            message_id=message_,
            media=await get_input_media_hero_image(
                "sort",
                "Как отсортировать результат?"
            ),
            reply_markup=await sort_kb()
        )
    except CustomError as error:
        msg, photo = await get_error_answer_photo(error)
        await message.answer_photo(
            photo=photo,
            caption=msg,
            reply_markup=await menu_kb()
        )


@search.callback_query(ItemFSM.sort, F.data.in_(SORT_SET))
async def search_qnt(callback: CallbackQuery, state: FSMContext) -> None:
    """
    
    :param callback: 
    :param state: 
    :return: 
    """
    try:
        await state.update_data(sort=callback.data)
        await state.set_state(ItemFSM.qnt)
        await callback.message.edit_media(
            media=await get_input_media_hero_image(
                "quantity",
                "сколько единиц товара вывести?"),
            reply_markup=await qnt_kb()
        )
    except CustomError as error:
        await callback.message.edit_media(
            media=await get_error_answer_media(error),
            reply_markup=await menu_kb()
        )


@search.callback_query(ItemFSM.qnt, F.data.in_(QNT))
async def search_result(call: CallbackQuery, state: FSMContext) -> None:
    """
    
    :param call: 
    :param state: 
    :return: 
    """
    try:
        await state.update_data(qnt=call.data)
        data = await state.get_data()
        await call.answer("⌛ searching {0}".format(data['product']))

        result = await request_item_list(
            q=data.get("product"),
            sort=data.get("sort"),
            url=config.URL_API_ITEM_LIST
        )
        try:
            if result["message"] is not None:
                raise FreeAPIExceededError(
                    message="❌ лимит API превышен\n{0}".format(
                        result.get('message')
                    )
                )
        except KeyError:
            pass

        item_list, price_range = await deserialize_item_list(
            response=result,
            user_id=call.from_user.id,
            data=data
        )
        data = await state.get_data()
        await call.message.answer('🔍  результат поиска:\n<b>{0:.50}</b>'.format(
            data['product'])
        )
        # await call.message.bot.delete_message(
        #     chat_id=call.message.chat.id,
        #     message_id=call.message.message_id
        # )
        for msg, img, kb in item_list:
            await asyncio.sleep(0.5)
            await call.message.answer_photo(photo=img, caption=msg, reply_markup=kb)
        await call.message.answer(
            text='По запросу {0}\n найдено {1}\nв ценовой диапазоне {2}'.format(
                data['product'],
                len(item_list),
                price_range
            ),
            reply_markup=await menu_kb()
        )
        await state.clear()

    except FreeAPIExceededError as error:
        await call.message.answer("⚠️ Ошибка\n{0}".format(str(error)))
    except CustomError as error:
        msg, photo = await get_error_answer_photo(error)
        await call.message.answer_photo(photo=photo, caption=msg)


@search.callback_query(F.data.startswith("delete"))
async def search_delete_callback(callback: CallbackQuery) -> None:
    """

    :param callback:
    :return:
    """
    await callback.message.edit_media(
        media=await get_input_media_hero_image('error')
    )
