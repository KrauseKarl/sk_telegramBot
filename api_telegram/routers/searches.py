import uuid

from aiogram import F, Router
from aiogram.filters import Command, or_f
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey
from aiogram.types import CallbackQuery, Message

from api_aliexpress.deserializers import *
from api_aliexpress.request import *
from api_redis.handlers import *
from api_telegram.callback_data import *
from api_telegram.crud.items import *
from api_telegram.keyboards import *
from api_telegram.paginations import *
from api_telegram.statments import *
from database.exceptions import *
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
        #     await state.set_state(ItemFSM.product)
        #
        #     await message.edit_media(
        #         media=await get_input_media_hero_image(
        #             "search",
        #             "🛍️ Введите название товара."),
        #         reply_markup=await main_keyboard()
        #     )
        # except TelegramBadRequest:
        await state.clear()
        await state.set_state(ItemFSM.product)
        await message.answer_photo(
            photo=await get_fs_input_hero_image("search"),
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
        await redis_flush_keys()
        await state.update_data(product=message.text)

        await message.bot.edit_message_media(
            chat_id=message.chat.id,
            message_id=int(message.message_id) - 1,
            media=await get_input_media_hero_image(
                "range",
                "Задать ценовой диапазон?"
            ),
            reply_markup=await price_range_kb()
        )
        await message.bot.delete_message(
            chat_id=message.chat.id,
            message_id=message.message_id
        )

    except TelegramBadRequest:
        await message.answer_photo(
            photo=await get_fs_input_hero_image("range"),
            caption="Задать ценовой диапазон?",
            reply_markup=await price_range_kb()
        )
    except CustomError as error:
        msg, photo = await get_error_answer_photo(error)
        await message.answer_photo(
            photo=photo,
            caption=msg,
            reply_markup=await error_kb()
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
        prev_message = int(message.message_id) - 2

        await message.bot.delete_message(
            chat_id=message.chat.id,
            message_id=message.message_id
        )
        min_price = message.text
        if int(min_price) < 1:
            raise CustomError(
                "Минимальная цена не должна быть отрицательной\t"
                "🔄\tпопробуйте еще раз"
            )
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
        prev_message = int(message.message_id) - 3
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

# 🟥 callback_kb= 'item_list_aa8a5340-7512-4ecc-b471-4cda077687e9_2'


# class NumbersCallbackFactory(CallbackData, prefix="fabnum"):
#     action: str
#     value: Optional[int] = None
#
#     builder.button(
#         text="-2", data=NumbersCallbackFactory(action="change", value=-2)
#     )
# InlineKeyboardButton(
#     text="demo",
#     data=MyCallback(foo="demo", bar="42").pack()  # value should be packed to string
# )
#
# @router.callback_query(MyCallback.filter(F.foo == "demo"))
# async def my_callback_foo(query: CallbackQuery, data: MyCallback):
#     await query.answer(...)
#     ...
#     print("bar =", data.bar)


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
#         #####################################################################
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

async def check_current_state(
        state: FSMContext,
        callback: CallbackQuery
) -> bool:
    """

    :param state:
    :param callback:
    :return:
    """
    key = StorageKey(
        bot_id=callback.bot.id,
        chat_id=callback.message.chat.id,
        user_id=callback.from_user.id
    )
    return bool(await state.storage.get_state(key))


async def create_uuid_key(length: int) -> str:
    """

    :param length:
    :return:
    """
    return "{0:.10}".format(str(uuid.uuid4().hex)[:length])


async def get_or_create_key(data, user_id):
    if data and await orm_get_query_from_db(data.key):
        return data.key, False
    # elif await orm_get_query_by_id_from_db(user_id):
    #     return await orm_get_query_by_id_from_db(user_id)
    else:
        new_key = await create_uuid_key(6)
        print(f'🔑🔑🔑 NEW KEY {new_key}')
        return new_key, True


@search.callback_query(
    or_f(ItemFSM.sort,
         ItemCBD.filter(),
         DetailCBD.filter(F.action == DetailAction.back_list)
         )

)
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
    print("=" * 50)
    # print(f"️\n⬛️🟨 ENDPOINT SEARCH RESULT\n⬛️🟨{callback_data=}")

    try:
        ####################################################################################
        is_state = await check_current_state(state, callback)

        if is_state:
            await state.update_data(sort=callback.data)
            state_data = await state.get_data()
            await state.set_state(state=None)

            api_page = 1
            page = 1
            key, created = await get_or_create_key(callback_data, callback.from_user.id)

            callback_data = ItemCBD(
                key=key if created else callback_data.key,
                api_page=api_page,
                page=str(page)
            )
            data = dict(
                q=state_data.get('product'),
                sort=state_data.get('sort'),
                page=api_page,
                startPrice=state_data.get('price_min'),
                endPrice=state_data.get('price_max'),
                user_id=callback.from_user.id,
                command='search'
            )
            if created:
                await save_query_in_db(data, key, page)

        else:
            state_data = await state.get_data()
            print(f"️⬛️🟨 {callback_data=}")
            data = dict(
                q=state_data.get('product'),
                sort=state_data.get('sort'),
                page=callback_data.api_page,
                startPrice=state_data.get('price_min'),
                endPrice=state_data.get('price_max'),
                user_id=callback.from_user.id,
                command='search'
            )
        print(f"️⬛️🟨 {state_data=}")
        print("️⬛️🟨 data q={0} page={1}".format(data.get('q', None), data.get('page', None)))
        #####################################################################################
        params = await get_paginate_item(data, callback_data)
        ####################################################################################
        kb = await paginate_item_list_kb(params, callback_data.api_page)
        photo = await create_tg_answer(params)
        #####################################################################################
        print("=" * 50)
        await callback.message.edit_media(media=photo, reply_markup=kb)
    except CustomError as error:
        # msg, photo = await get_error_answer_photo(error)
        # await call.message.answer_photo(photo=photo, caption=msg)
        await callback.answer(text=str(error), show_alert=True)


@search.callback_query(F.data.startswith("delete"))
async def search_delete_callback(callback: CallbackQuery) -> None:
    """

    :param callback:
    :return:
    """
    await callback.message.edit_media(
        media=await get_input_media_hero_image('error')
    )


@search.message(Command("redis"))
async def get_key_cache(message: Message):
    print('redis route start')
    await redis_get_keys()
    print('redis route finish')


@search.message(Command("del"))
async def get_key_cache(message: Message):
    print('redis route start')
    await redis_flush_keys()
    print('redis route finish')
