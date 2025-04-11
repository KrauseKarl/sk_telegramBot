from aiogram import F, Router, types as t
from aiogram.filters import Command

from api_redis import RedisHandler
from api_telegram import kbm, ItemCBD, DetailCBD, DetailAction
from api_telegram.crud import ItemManager
from api_telegram.statments import *
from database.exceptions import *
from utils.cache_key import *
from utils.media import *
from utils.validators import min_price_validator, max_price_validator

search = Router()


async def delete_prev_message(message: t.Message):
    await message.bot.delete_message(
        chat_id=message.chat.id,
        message_id=message.message_id
    )
    return int(message.message_id) - 1


# ITEM LIST ############################################################################################################
@search.message(Command("search"))
async def search_name_message(message: t.Message, state: FSMContext) -> None:
    """
    
    :param message:
    :param state: 
    :return: 
    """
    try:
        await state.clear()
        await state.set_state(ItemFSM.product)
        await message.answer_photo(
            photo=await get_fs_input_hero_image("search"),
            caption="🛍️ Введите название товара."
        )
    except CustomError as error:
        await message.edit_media(
            media=await get_error_answer_media(error),
            reply_markup=await kbm.menu()
        )


@search.callback_query(F.data.startswith("search"))
async def search_name_callback(callback: t.CallbackQuery, state: FSMContext) -> None:
    """
    Request product name.

    :param callback: CallbackQuery
    :param state: FSMContext
    :return: None
    """
    try:
        await state.clear()

        # todo REDIS KEY CLEAR

        await state.set_state(ItemFSM.product)

        await callback.message.edit_media(
            media=await get_input_media_hero_image(
                "search",
                "🛍️ {0}, Введите название товара.".format(
                    callback.from_user.username
                )
            )
        )
        # await callback.message.answer_photo(
        #     photo=await get_fs_input_hero_image("search"),
        #     caption="🛍️ Введите название товара.",
        #     reply_markup=await main_keyboard()
        # )
    except CustomError as error:
        await callback.message.edit_media(
            media=await get_error_answer_media(error),
            reply_markup=await kbm.menu()
        )


@search.message(ItemFSM.product)
async def search_price_range(message: t.Message, state: FSMContext) -> None:
    """

    :param message:
    :param state:
    :return:
    """
    try:

        await RedisHandler().flush_keys()
        await state.update_data(product=message.text)

        await message.bot.edit_message_media(
            chat_id=message.chat.id,
            message_id=int(message.message_id) - 1,
            media=await get_input_media_hero_image(
                "range",
                "Задать ценовой диапазон?"
            ),
            reply_markup=await kbm.price_range()
        )
        await message.bot.delete_message(
            chat_id=message.chat.id,
            message_id=message.message_id
        )

    except TelegramBadRequest:
        await message.answer_photo(
            photo=await get_fs_input_hero_image("range"),
            caption="Задать ценовой диапазон?",
            reply_markup=await kbm.price_range()
        )
    except CustomError as error:
        await message.answer(
            text=f"⚠️ Ошибка\n{str(error)}",
            show_alert=True
        )


@search.callback_query(F.data.startswith("price_min"))
async def search_price_min(callback: t.CallbackQuery, state: FSMContext) -> None:
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
        await callback.answer(
            text=f"⚠️ Ошибка\n{str(error)}",
            show_alert=True
        )


@search.message(ItemFSM.price_min)
async def search_price_max(message: t.Message, state: FSMContext) -> None:
    """

    :param message:
    :param state:
    :return:
    """
    try:
        prev_message = int(message.message_id) - 2

        await message.bot.delete_message(
            chat_id=message.chat.id,
            message_id=message.message_id
        )
        min_price = message.text
        await min_price_validator(min_price)
        await state.update_data(price_min=min_price)
        await state.set_state(ItemFSM.price_max)

        await message.bot.edit_message_media(
            chat_id=message.chat.id,
            message_id=prev_message,
            media=await get_input_media_hero_image(
                "price_max",
                "Укажите максимальную цену?"
            )
        )
        # await message.answer_photo(
        #     photo=await get_fs_input_hero_image("price_max"),
        #     caption="Укажите максимальную цену?"
        # )
    except (CustomError, ValueError) as error:
        await message.answer(
            text=f"⚠️ Ошибка\n{str(error)}",
            show_alert=True
        )


# SORT #####################################################################
@search.message(ItemFSM.price_max)
async def search_sort(message: t.Message, state: FSMContext) -> None:
    """
    
    :param message: 
    :param state: 
    :return: 
    """
    try:
        prev_message = int(message.message_id) - 3
        await message.bot.delete_message(
            chat_id=message.chat.id,
            message_id=message.message_id
        )
        min_price = int(await state.get_value('price_min'))
        max_price = int(message.text)
        await min_price_validator(min_price)
        await max_price_validator(min_price, max_price)
        await state.update_data(price_max=max_price)
        await state.set_state(ItemFSM.sort)

        await message.bot.edit_message_media(
            chat_id=message.chat.id,
            message_id=prev_message,
            media=await get_input_media_hero_image(
                "sort",
                "Как отсортировать результат?"
            ),
            reply_markup=await kbm.sort()
        )
    except (CustomError, ValueError) as error:
        await message.answer(
            text=f"⚠️ Ошибка\n{str(error)}",
            show_alert=True
        )


@search.callback_query(F.data.startswith("price_skip"))
async def search_sort_call(callback: t.CallbackQuery, state: FSMContext) -> None:
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
            reply_markup=await kbm.sort()
        )
    except CustomError as error:
        await callback.answer(
            text=f"⚠️ Ошибка\n{str(error)}",
            show_alert=True
        )


# SORT #####################################################################

# @search.callback_query(ItemFSM.sort, F.data.in_(SORT_SET))
# async def search_qnt(callback: CallbackQuery, state: FSMContext) -> None:
#     """
#
#     :param callback:
#     :param state:
#     :return:
#     """
#     try:
#         await state.update_data(sort=callback.data)
#         # await state.set_state(ItemFSM.qnt)
#
#         await callback.message.edit_media(
#             media=await get_input_media_hero_image(
#                 "quantity",
#                 "сколько единиц товара вывести?"),
#             reply_markup=await qnt_kb()
#         )
#     except CustomError as error:
#         await callback.message.edit_media(
#             media=await get_error_answer_media(error),
#             reply_markup=await menu_kb()
#         )


# @search.callback_query(ItemFSM.qnt, F.data.in_(QNT))
# @search.callback_query(F.data.startswith("item_list_next_page"))
# async def search_result_next_page(call: CallbackQuery, state: FSMContext) -> None:
#     """
#
#     :param call:
#     :param state:
#     :return:
#     """
#
#     try:
#         page = call.data.split("_")[-1]
#         print("🟨{0}🟨 SEARCH RESULT PAGE ".format(page))
#
#         data = await state.get_data()
#
#         await call.bot.delete_message(
#             chat_id=call.message.chat.id,
#             message_id=call.message.message_id
#         )
#
#         await call.message.answer("🟪 еще результаты стр {}".format(page).upper())
#         result = await request_api(
#             query=data.get("product"),
#             sort=data.get("sort"),
#             start_price=data.get("price_min"),
#             end_price=data.get("price_max"),
#             url=config.URL_API_ITEM_LIST,
#             page=str(page)
#         )
#
#         item_list, price_range = await deserialize_item_list(
#             response=result,
#             user_id=call.from_user.id,
#             data=data
#         )
#         for msg, img, kb in item_list:
#             # await asyncio.sleep(0.5)
#             await call.message.answer_photo(photo=img, caption=msg, reply_markup=kb)
#
#         msg = '<b>{0}</b>\  {1}'.format(data['product'], page)
#         page = int(page) + 1
#         kb = await kb_builder(
#             (2,),
#             [
#                 {'🏠 menu': "menu"},
#                 {"🛒 искать ещё": "search"},
#                 {f"➡️ следующая стр {page}": f"item_list_next_page_{page}"}
#             ]
#         )
#         await call.message.answer(text=msg, reply_markup=kb, parse_mode='HTML')
#
#     except FreeAPIExceededError as error:
#         await call.answer(show_alert=True, text="⚠️ ОШИБКА\n\n{0}".format(error))
#     except CustomError as error:
#         msg, photo = await get_error_answer_photo(error)
#         await call.message.answer_photo(photo=photo, caption=msg)


# @search.callback_query(
#     or_f(
#         ItemCBD.filter(),
#         DetailCBD.filter(F.action == DetailAction.back_list)
#     )
# )
# async def item_list_page(
#         callback: types.CallbackQuery,
#         state: FSMContext,
#         callback_data: ItemCBD | DetailCBD
# ) -> None:
#     """
#     Some.
#     :param callback_data:
#     :param state:
#     :param callback:
#     :return:
#     """
#     print('️\n🟦🟧🟦🟧🟦🟧 ENDPOINT SEARCH RESULT🟦🟧🟦🟧🟦🟧')
#     try:
#         data = await state.get_data()
#         params = await get_paginate_item(data, callback_data)
# #         #####################################################################
#         kb = await paginate_item_list_kb(params)
#         photo = await create_tg_answer(params)
#         #####################################################################
#         await callback.message.edit_media(media=photo, reply_markup=kb)
#         print('️🟦🟧🟦🟧🟦🟧🟦🟧🟦🟧🟦🟧')
#
#     except CustomError as error:
#         msg, photo = await get_error_answer_photo(error)
#         await callback.message.answer_photo(
#             photo=photo,
#             caption=msg,
#             reply_markup=await error_kb()
#         )

@search.callback_query(ItemFSM.sort)
@search.callback_query(ItemCBD.filter())
@search.callback_query(DetailCBD.filter(F.action == DetailAction.back_list))
async def search_result(
        callback: CallbackQuery,
        state: FSMContext,
        callback_data: ItemCBD | DetailCBD | None = None
) -> None:
    """

    :param callback_data:
    :param callback:
    :param state: 
    :return: 
    """
    try:
        await callback.answer()
        manager = ItemManager(
            state=state,
            callback=callback,
            callback_data=callback_data
        )
        await callback.message.edit_media(
            media=await manager.message(),
            reply_markup=await manager.keyboard()
        )
    except CustomError as error:
        await callback.answer(
            text=f"⚠️ Ошибка\n{str(error)}",
            show_alert=True
        )


@search.callback_query(F.data.startswith("delete"))
async def search_delete_callback(callback: CallbackQuery) -> None:
    """
    :param callback:
    :return:
    """
    await callback.message.edit_media(
        media=await get_input_media_hero_image('error')
    )
