import asyncio

from aiogram import Router, F
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


async def delete_prev_message(message: Message):
    await message.bot.delete_message(
        chat_id=message.chat.id,
        message_id=message.message_id
    )
    return int(message.message_id) - 1


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
    Request product name.

    :param callback: CallbackQuery
    :param state: FSMContext
    :return: None
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
async def search_price_range(message: Message, state: FSMContext) -> None:
    """

    :param message:
    :param state:
    :return:
    """
    try:
        prev_message = int(message.message_id) - 1
        await message.bot.delete_message(
            chat_id=message.chat.id,
            message_id=message.message_id
        )

        await state.update_data(product=message.text)

        kb = await kb_builder(
            (2,),
            [
                {"✅ да": "price_min"},
                {"🚫 пропустить": "price_skip"},
            ]

        )
        await message.bot.edit_message_media(
            chat_id=message.chat.id,
            message_id=prev_message,
            media=await get_input_media_hero_image(
                "range",
                "Задать ценовой диапазон?"
            ),
            reply_markup=kb
        )
    except CustomError as error:
        msg, photo = await get_error_answer_photo(error)
        await message.answer_photo(
            photo=photo,
            caption=msg,
            reply_markup=await menu_kb()
        )


@search.callback_query(F.data.startswith("price_min"))
async def search_price_min(callback: CallbackQuery, state: FSMContext) -> None:
    """

    :param callback:
    :param state:
    :return:
    """
    try:
        await state.set_state(ItemFSM.price_min)

        await callback.message.edit_media(
            media=await get_input_media_hero_image(
                "price_min",
                "Укажите минимальную  цену?"
            )
        )
    except CustomError as error:
        msg, photo = await get_error_answer_photo(error)
        await callback.message.answer_photo(
            photo=photo,
            caption=msg,
            reply_markup=await menu_kb()
        )


@search.message(ItemFSM.price_min)
async def search_price_max(message: Message, state: FSMContext) -> None:
    """

    :param message:
    :param state:
    :return:
    """
    try:
        # print(f"{message.message_id= }")
        # prev_message = int(message.message_id) - 1
        # print(f"{prev_message= }")
        # await message.bot.delete_message(
        #     chat_id=message.chat.id,
        #     message_id=message.message_id
        # )
        min_price = message.text
        if int(min_price) < 1:
            raise CustomError(
                "Минимальная цена не должна быть отрицательной\t"
                "🔄\tпопробуйте еще раз"
            )
        await state.update_data(price_min=min_price)
        await state.set_state(ItemFSM.price_max)

        # await message.bot.edit_message_media(
        #     chat_id=message.chat.id,
        #     message_id=prev_message,
        #     media=await get_input_media_hero_image(
        #         "price_max",
        #         "Укажите максимальную цену?"
        #     )
        # )
        await message.answer_photo(
            photo=await get_fs_input_hero_image("price_max"),
            caption="Укажите максимальную цену?"
        )
    except (CustomError, ValueError) as error:
        msg, photo = await get_error_answer_photo(error)
        await message.answer_photo(photo=photo, caption=msg)


# SORT #####################################################################
@search.message(ItemFSM.price_max)
async def search_sort(message: Message, state: FSMContext) -> None:
    """
    
    :param message: 
    :param state: 
    :return: 
    """
    try:
        prev_message = int(message.message_id) - 1
        await message.bot.delete_message(
            chat_id=message.chat.id,
            message_id=message.message_id
        )
        min_price = int(await state.get_value('price_min'))
        max_price = int(message.text)

        if int(max_price) < 1:
            raise CustomError(
                "Максимальная цена не должна быть отрицательной\t"
                "🔄\tпопробуйте еще раз"
            )
        if min_price > max_price:
            raise CustomError(
                "Максимальная цена должна быть больше минимальной\t"
                "🔄\tпопробуйте еще раз"
            )
        await state.update_data(price_max=max_price)
        await state.set_state(ItemFSM.sort)

        await message.bot.edit_message_media(
            chat_id=message.chat.id,
            message_id=prev_message,
            media=await get_input_media_hero_image(
                "sort",
                "Как отсортировать результат?"
            ),
            reply_markup=await sort_kb()
        )
    except (CustomError, ValueError) as error:
        msg, photo = await get_error_answer_photo(error)
        await message.answer_photo(photo=photo, caption=msg)


@search.callback_query(F.data.startswith("price_skip"))
async def search_sort_call(callback: CallbackQuery, state: FSMContext) -> None:
    """

        :param callback: CallbackQuery
        :param state: FSMContext
        :return: None
        """
    try:
        await state.set_state(ItemFSM.sort)

        await callback.message.edit_media(
            media=await get_input_media_hero_image(
                "sort",
                "Как отсортировать результат?"
            ),
            reply_markup=await sort_kb()
        )
    except CustomError as error:
        msg, photo = await get_error_answer_photo(error)
        await callback.message.answer_photo(
            photo=photo,
            caption=msg,
            reply_markup=await menu_kb()
        )


# SORT #####################################################################

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

        result = await request_api(
            query=data.get("product"),
            sort=data.get("sort"),
            start_price=data.get("price_min"),
            end_price=data.get("price_max"),
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

        msg = 'По запросу\t<b>{0}</b>\n'.format(data['product'])
        if data.get("price_min") and data.get("price_max"):
            msg += 'цена от {0} до {1} руб.\n'.format(
                data.get("price_min"),
                data.get("price_max")
            )
        msg += 'найдено {0} ед.\nценовой диапазон: {1} руб.'.format(
            len(item_list),
            price_range
        )
        kb = await kb_builder(
            (2,),
            [
                {'🏠 menu': "menu"},
                {"🛒 искать ещё": "search"}
            ]
        )
        await call.message.answer(text=msg, reply_markup=kb, parse_mode='HTML')
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
