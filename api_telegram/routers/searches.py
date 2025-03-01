import uuid

from aiogram import F, Router
from aiogram.filters import Command, or_f
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from api_aliexpress.deserializers import *
from api_aliexpress.request import *
from api_redis.handlers import *
from api_telegram.callback_data import *
from api_telegram.crud.items import *
from api_telegram.keyboards import *
from api_telegram.paginations import paginate_item_list_kb
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


@search.callback_query(
    or_f(
        ItemCBD.filter(),
        DetailCBD.filter(F.action == DetailAction.back_list)
    )
)
async def item_list_page(
        callback: types.CallbackQuery,
        state: FSMContext,
        callback_data: ItemCBD | DetailCBD
) -> None:
    """
    Some.
    :param callback_data:
    :param state:
    :param callback:
    :return:
    """

    try:
        data = await state.get_data()
        # print('⬜️🟧 ENDPOINT SEARCH PAGINATION')
        key = callback_data.key
        page = int(callback_data.page)
        api_page = callback_data.api_page

        paginator = await get_paginate_item(data, callback_data)
        item = paginator.get_page()[0]

        kb = await paginate_item_list_kb(
            item_id=str(item['item']['itemId']),
            key=key,
            api_page=api_page,
            page=int(page),
            len_data=paginator.len
        )
        photo = await create_tg_answer(item["item"], page, api_page, paginator.pages)
        await callback.message.edit_media(media=photo, reply_markup=kb)

        for i in kb:
            for k in i[1]:
                callback = k[0].callback_data
                if callback.startswith("ITD"):
                    print('❤️ list to detail', callback.split(":"))
    except CustomError as error:
        msg, photo = await get_error_answer_photo(error)
        await callback.message.answer_photo(
            photo=photo,
            caption=msg,
            reply_markup=await error_kb()
        )
        # await callback.answer(text=str(error), show_alert=True)


@search.callback_query(ItemFSM.sort)
async def search_result(call: CallbackQuery, state: FSMContext) -> None:
    """

    :param call:
    :param state: 
    :return: 
    """
    # print('️⬛️🟨 ENDPOINT SEARCH RESULT')

    try:
        await state.update_data(sort=call.data)
        api_page = 1
        paginator_page = 1
        key = str(uuid.uuid4().hex)[:8]
        data = await save_query_in_cache_state(state)
        # print(f'️⬛️🟨 {data= }')
        ################################################################################################################
        call_data = ItemCBD(key=key, api_page="0", page=str(paginator_page))
        paginator = await get_paginate_item(data, call_data)
        # if config.FAKE_MODE:
        #     result = await request_api_fake(page=paginator_page, query=data.get("product"))
        # else:
        #     result = await request_api(
        #         query=data.get("product"),
        #         sort=data.get("sort"),
        #         start_price=data.get("price_min"),
        #         end_price=data.get("price_max"),
        #         url=config.URL_API_ITEM_LIST,
        #         page=str(api_page)
        #     )
        #
        # response_list = result["result"]["resultList"]
        # cache_data = await redis_get_data_from_cache(cache_key)
        # if cache_data is None:
        #     await redis_set_data_to_cache(key=cache_key, value=response_list)
        # item_list_cache = await redis_get_data_from_cache(cache_key)
        #
        # paginator = Paginator(array=item_list_cache, page=paginator_page)
        ################################################################################################################
        item = paginator.get_page()[0]
        # sort_price_set = set(sorted([item["item"]["sku"]["def"]["promotionPrice"] for item in item_list_cache]))
        # price_range_list = '{0} - {1}'.format(min(sort_price_set), max(sort_price_set))
        kb = await paginate_item_list_kb(
            item_id=str(item['item']['itemId']),
            key=key,
            api_page=str(api_page),
            page=int(paginator_page),
            len_data=paginator.len
        )
        await orm_make_record_request(
            HistoryModel(
                user=call.from_user.id,
                command='search',
                # price_range=''.format(data.get('price_min'), data.get('price_max')),
                price_min=data.get('price_min', None),
                price_max=data.get('price_max', None),
                search_name=data.get('product', None),
                sort=config.SORT_DICT[data.get('sort', "default")]
            ).model_dump())
        photo = await create_tg_answer(item["item"], paginator_page, paginator.len, api_page)
        await call.message.edit_media(media=photo, reply_markup=kb)

    except CustomError as error:
        # msg, photo = await get_error_answer_photo(error)
        # await call.message.answer_photo(photo=photo, caption=msg)
        await call.answer(text=str(error), show_alert=True)


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
