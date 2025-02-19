import uuid

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, ReplyKeyboardMarkup, KeyboardButton

from data_api.deserializers import *
# from data_api.request import *
from database.exceptions import *
from telegram_api.statments import *
from utils.media import *
from redis_api.handlers import *

search = Router()


async def delete_prev_message(message: Message):
    await message.bot.delete_message(
        chat_id=message.chat.id,
        message_id=message.message_id
    )
    return int(message.message_id) - 1


async def main_keyboard():
    kb_list = [
        [KeyboardButton(text="Menu")]
    ]
    # if user_telegram_id in admins:
    #     kb_list.append([KeyboardButton(text="⚙️ Админ панель")])
    kb = ReplyKeyboardMarkup(
        keyboard=kb_list,
        resize_keyboard=True,
        # one_time_keyboard=True
        input_field_placeholder='stars'
    )
    return kb


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
            caption="🛍️ Введите название товара.",
            reply_markup=await menu_kb()
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
        # st = RedisStorage()
        await redis_flush_keys()
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
#         text="-2", callback_data=NumbersCallbackFactory(action="change", value=-2)
#     )
# InlineKeyboardButton(
#     text="demo",
#     callback_data=MyCallback(foo="demo", bar="42").pack()  # value should be packed to string
# )
#
# @router.callback_query(MyCallback.filter(F.foo == "demo"))
# async def my_callback_foo(query: CallbackQuery, callback_data: MyCallback):
#     await query.answer(...)
#     ...
#     print("bar =", callback_data.bar)
async def request_api_fake(page: str | int):
    path = os.path.join(config.BASE_DIR, "_json_example", "list_{0}.json".format(page))
    with open(path, 'r') as file:
        data = json.load(file)
    return data


class CacheKey(CallbackData, prefix='redis'):
    key: str
    api_page: str
    # paginate_page: str


class ItemCBD(CallbackData, prefix='itList'):
    key: str
    api_page: int | str
    paginate_page: int | str


@search.callback_query(ItemCBD.filter())  # F.data.startswith("itList"))
async def item_list_page(
        callback: types.CallbackQuery,
        state: FSMContext,
        callback_data: ItemCBD
) -> None:
    """
    Some.
    :param callback_data:
    :param state:
    :param callback:
    :return:
    """
    try:
        print(f'🟠SEARCH PAGINATION LIST ENDPOINT🟠🟠🟠🟠🟠🟠🟠🟠🟠🟠🟠🟠🟠🟠🟠🟠🟠🟠🟠🟠\n🟠{callback.data= }')
        await callback.answer("🟠 SEARCH PAGINATION")

        #  itList : 86fa2539fafd4476b66b27ac725e372b : 1 : 1
        key = callback_data.key
        paginate_page = int(callback_data.paginate_page)
        prev_paginate_page = str(paginate_page - 1)
        api_page = callback_data.api_page

        cache_key = CacheKey(key=key, api_page=api_page).pack()
        print(f"\n🟠 {cache_key}\n🟠 {api_page= }\n🟠 {paginate_page= }\n")

        item_list_cache = await redis_get_data_from_cache(cache_key)
        print("__________🟩", paginate_page, len(item_list_cache), int(paginate_page) <= len(item_list_cache), '🟩______________')
        if int(paginate_page) <= len(item_list_cache):
            print("🟩🟩 CACHE DATA", int(paginate_page) <= len(item_list_cache))
            paginator = Paginator(array=item_list_cache, page=paginate_page)
            one_item = paginator.get_page()[0]
        else:
            print("🟥🟥 NEW REQUIEST", int(paginate_page) <= len(item_list_cache))
            new_api_page = str(int(api_page) + 1)
            result = await request_api_fake(page=api_page)
            item_list_cache = result["result"]["resultList"]
            new_cache_key = CacheKey(key=key, api_page=new_api_page).pack()
            print(f"🟪\t{new_cache_key= }🟪\t{new_api_page= }\n🟪\t{len(item_list_cache)= }\n")
            paginate_page = 1
            api_page = new_api_page
            cache_key = new_cache_key
            cache_data = await redis_get_data_from_cache(cache_key)
            if cache_data is None:
                await redis_set_data_to_cache(key=cache_key, value=item_list_cache)
            paginator = Paginator(array=item_list_cache, page=paginate_page)
            one_item = paginator.get_page()[0]

        ##########################################################################################
        keyboard_list = []
        ##########################################################################################
        if int(api_page) == 1 and int(paginate_page) == 1:
            print("⭐️ 1й запрос и 1 я страница")
            # ✅ next = 2
            next_kb = ItemCBD(key=key, api_page=api_page, paginate_page=2).pack()
            # ✅ last = paginator.pages
            last_kb = ItemCBD(key=key, api_page=api_page, paginate_page=str(paginator.pages)).pack()
            # ❌ prev None
            # ❌ fist None
            keyboard_list.extend([{"След. ➡️": next_kb}, {"После. ⏩": last_kb}])
            print(f"🟩 [❌] ❌ НАЗАД  ВПЕРЕД {next_kb} [{last_kb}]")

        elif int(api_page) > 1 and int(paginate_page) == 1:
            print("⭐️ Следующий запрос и 1я страница")
            # ✅ next = 2
            next_kb = ItemCBD(key=key, api_page=api_page, paginate_page=2).pack()
            # ✅ last = paginator.pages
            last_kb = ItemCBD(key=key, api_page=api_page, paginate_page=str(paginator.pages)).pack()
            # ✅ prev = "itList:cache_key:api_page-1:prev(paginator.pages)" ! after 2nd request to redis by pre_cache_key
            prev_kb = ItemCBD(key=key, api_page=str(int(api_page) - 1), paginate_page=prev_paginate_page).pack()
            # ❌ fist None
            print(f"🟩 [❌]  {prev_kb} НАЗАД  ВПЕРЕД {next_kb} [{last_kb}]")
            keyboard_list.extend([{"След. ➡️": next_kb}, {"⬅️ Пред.": prev_kb}, {" После. ⏩": last_kb}])

        elif int(paginate_page) > 1 and int(paginate_page) < paginator.pages:
            print("⭐️ следующая страница")
            # ✅ next = paginate_page + 1 if paginate_page + 1 < paginator.pages else paginator.pages
            next_page = str(paginate_page + 1 if paginate_page + 1 < paginator.pages else paginator.pages + 1)
            next_kb = ItemCBD(key=key, api_page=api_page, paginate_page=next_page).pack()
            # ✅ last = paginator.pages
            last_kb = ItemCBD(key=key, api_page=api_page, paginate_page=str(paginator.pages)).pack()
            # ✅ prev = paginate_page - 1  if paginate_page - 1 > 1 else 1
            prev_page = str(paginate_page - 1 if paginate_page - 1 > 1 else 1 )
            prev_kb = ItemCBD(key=key, api_page=api_page, paginate_page=prev_page).pack()
            # ✅ fist = 1
            first_kb = ItemCBD(key=key, api_page=api_page, paginate_page=str(1)).pack()
            keyboard_list.extend(
                [{"След. ➡️": next_kb}, {"⬅️ Пред.": prev_kb}, {"⏪ Первая ": first_kb}, {" После. ⏩": last_kb}])
            print(f"🟩 [{first_kb}]  {prev_kb} НАЗАД  ВПЕРЕД {next_kb} [{last_kb}]")

        elif int(paginate_page) == paginator.pages:
            print("⭐️ последняя страница")
            # ✅ next = request to api with api_page + 1
            next_kb = ItemCBD(key=key, api_page=api_page, paginate_page=str(paginate_page + 1)).pack()
            # ❌ last None
            # ✅ prev paginate_page - 1 if paginate_page - 1 != 0  else 1
            prev_page = str(paginate_page - 1 if paginate_page - 1 != 0 else 1)
            prev_kb = ItemCBD(key=key, api_page=api_page, paginate_page=prev_page).pack()
            # ✅ fist = 1
            first_kb = ItemCBD(key=key, api_page=api_page, paginate_page=str(1)).pack()
            keyboard_list.extend([{"След. ➡️": next_kb}, {"⬅️ Пред.": prev_kb},   {"⏪ Первая ": first_kb}])
            print(f"🟩 [{first_kb}]  {prev_kb} НАЗАД  ВПЕРЕД {next_kb} [❌]")
        else:
            print('\n❌❌❌❌❌❌KB ERROR ❌❌❌❌❌❌❌\n')
        ##########################################################################################
        keyboard_list.extend([{"подробно": "item_{0}".format(one_item['item']['itemId'])}, {"menu": "menu"}])
        ##########################################################################################

        # try:
        #
        #     if int(paginate_page) == 1:
        #         next_page = str(paginator.pages if paginate_page + 1 > paginator.pages else paginate_page + 1)
        #         next_kb = ItemCBD(key=key, api_page=api_page, paginate_page=next_page).pack()
        #
        #         prev_page = str(1 if paginate_page - 1 < 1 else paginate_page - 1)
        #         prev_kb = ItemCBD(key=key, api_page=api_page, paginate_page=str(paginate_page - 1)).pack()
        #         print(f"🟩🟩🟩\nНАЗАД {prev_kb}<<  >>{next_kb} ВПЕРЕД\n🟩🟩🟩")
        #
        #         if int(prev_page) != 1:
        #             first_kb = ItemCBD(key=key, api_page=api_page, paginate_page=str(1)).pack()
        #             print(f"🟩🟩🟩\nпервая {first_kb } [{paginator.pages}]\n🟩🟩🟩")
        #
        #         if int(next_page) < int(paginator.pages):
        #             last_kb = ItemCBD(key=key, api_page=api_page, paginate_page=str(paginator.pages)).pack()
        #             print(f"🟩🟩🟩\nпоследняя {last_kb= } [{paginator.pages}]\n🟩🟩🟩")
        #
        #     if int(api_page) > 1 and int(paginate_page) == 1:
        #         prev_cache_key = CacheKey(key=key, api_page=str(int(api_page) - 1)).pack()
        #         last_prev_page_item = len(await redis_get_data_from_cache(prev_cache_key))
        #         prev_request_page = ItemCBD(
        #             key=key,
        #             api_page=str(int(api_page) - 1),
        #             paginate_page=last_prev_page_item
        #         ).pack()
        #         last_kb = ItemCBD(key=key, api_page=api_page, paginate_page=str(paginator.pages)).pack()
        #         print(f'***🟠🟠🟠 {prev_cache_key= } ')
        #         print(f'***🟠🟠🟠 {prev_request_page= } ')
        #
        #         kb = await kb_builder(
        #             size=(2, 1, 2),
        #             data_list=[
        #                 {"🟠️⬅️ Пред. стр.": prev_request_page},
        #                 {"След. ➡️": next_kb},
        #                 {"После. ": last_kb},
        #                 {"подробно": "item_{0}".format(one_item['item']['itemId'])},
        #                 {"menu": "menu"}
        #             ]
        #         )
        #
        # except IndexError:
        #
        #     print("🟥🟥🟥🟥🟥🟥🟥🟥🟥🟥🟥 IndexError | get new request_api")
        #     api_page = str(int(api_page) + 1)
        #     ############################################################################################################
        #     # data = await state.get_data()
        #     # result = await request_api(
        #     #     query=data.get("product"),
        #     #     sort=data.get("sort"),
        #     #     start_price=data.get("price_min"),
        #     #     end_price=data.get("price_max"),
        #     #     url=config.URL_API_ITEM_LIST,
        #     #     page=api_page
        #     # )
        #     ############################################################################################################
        #     result = await request_api_fake(page=api_page)
        #     #######################################
        #
        #     pre_paginate_page = paginator_page
        #     paginator_page = 1
        #
        #     item_list_cache = result["result"]["resultList"]
        #     cache_key_new = CacheKey(key=key, api_page=api_page).pack()
        #
        #     print(f"🟪\t{len(item_list_cache)= }\n🟪\t{api_page= }\n🟪\t{cache_key= }\n🟪\t{cache_key_new= }")
        #
        #     cache_key = cache_key_new
        #     cache_data = await redis_get_data_from_cache(cache_key)
        #
        #     if cache_data is None:
        #         value = json.dumps(item_list_cache, ensure_ascii=False, indent=4)
        #         await redis_set_data_to_cache(key=cache_key, value=value)
        #     paginator = Paginator(array=item_list_cache, page=1)
        #     one_item = paginator.get_page()[0]
        #
        #     next_page = str(paginator.pages if paginator_page + 1 > paginator.pages else paginator_page + 1)
        #     next_kb = ItemCBD(key=key, api_page=api_page, paginate_page=next_page).pack()
        #
        #     prev_page = str(1 if paginator_page - 1 < 1 else paginator_page - 1)
        #     prev_kb = ItemCBD(key=key, api_page=api_page, paginate_page=str(paginator_page - 1)).pack()
        #     print(f"🟥🟥🟥\nНАЗАД {prev_kb}<<  >>{next_kb} ВПЕРЕД\n🟥🟥🟥")
        #     if int(prev_page) != 1:
        #         first_kb = ItemCBD(key=key, api_page=api_page, paginate_page=str(1)).pack()
        #         print(f"🟥🟥🟥\nпервая {first_kb} [{paginator.pages}]\n🟥🟥🟥")
        #     if int(next_page) < int(paginator.pages):
        #         last_kb = ItemCBD(key=key, api_page=api_page, paginate_page=str(paginator.pages)).pack()
        #         print(f"🟥🟥🟥\nпоследняя {last_kb= } [{paginator.pages}]\n🟥🟥🟥")
        #
        #
        # if int(paginator_page) == 1:
        #     if int(api_page) != 1:
        #
        #         prev_cache_key = CacheKey(key=key, api_page=str(int(api_page) - 1)).pack()
        #         last_prev_page_item = len(await redis_get_data_from_cache(prev_cache_key))
        #         prev_request_page = ItemCBD(
        #             key=key,
        #             api_page=str(int(api_page) - 1),
        #             paginate_page=last_prev_page_item
        #         ).pack()
        #
        #         print(f'***🟠🟠🟠 {prev_cache_key= } ')
        #         print(f'***🟠🟠🟠 {prev_request_page= } ')
        #
        #         kb = await kb_builder(
        #             size=(2, 1, 2),
        #             data_list=[
        #                 {"🟠️⬅️ Пред. стр.": prev_request_page},
        #                 {"След. ➡️": next_kb},
        #                 {"После. ": last_kb},
        #                 {"подробно": "item_{0}".format(one_item['item']['itemId'])},
        #                 {"menu": "menu"}
        #             ]
        #         )
        #     else:
        #         kb = await kb_builder(
        #             size=(2, 1, 2),
        #             data_list=[
        #                 {"След. ➡️": next_kb},
        #                 {"После. ": last_kb},
        #                 {"подробно": "item_{0}".format(one_item['item']['itemId'])},
        #                 {"menu": "menu"}
        #             ]
        #         )
        #
        # else:  # page > 1:
        #     kb = await kb_builder(
        #         size=(2, 2, 2),
        #         data_list=[
        #             {"⬅️ Пред.": prev_kb},
        #             {"След. ➡️": next_kb},
        #             {"⏪ Первая ": first_kb},
        #             {" После. ⏩": last_kb},
        #             {"подробно": "item_{0}".format(one_item['item']['itemId'])},
        #             {"menu": "menu"}
        #         ]
        #     )

        msg = "{0:.50}\n".format(one_item["item"]["title"])
        msg += "👀\t{0}\n".format(one_item["item"]["sales"])
        msg += "💰\t{0} RUB\n".format(one_item["item"]["sku"]["def"]["promotionPrice"])
        msg += "{0}\n\n".format(one_item["item"]["itemUrl"])
        msg += "{0} из {1} стр. {2}".format(paginate_page, paginator.pages, api_page)
        img = ":".join(["https", one_item["item"]["image"]])
        photo = types.InputMediaPhoto(media=img, caption=msg, show_caption_above_media=False)

        kb = await builder_kb(keyboard_list, (2, 2, 1,))

        await callback.message.edit_media(media=photo, reply_markup=kb)

    except CustomError as error:
        msg, photo = await get_error_answer_photo(error)
        await callback.message.answer_photo(
            photo=photo,
            caption=msg,
            reply_markup=await menu_kb()
        )


@search.callback_query(ItemFSM.sort)
async def search_result(call: CallbackQuery, state: FSMContext) -> None:
    """
    
    :param call: 
    :param state: 
    :return: 
    """
    print("🟩🟩🟩  SEARCH RESULT")
    await call.answer("✅  SEARCH PAGINATION")

    try:
        await state.update_data(sort=call.data)
        api_page = 1
        ################################################################################################################
        # data = await state.get_data()
        # result = await request_api(
        #     query=data.get("product"),
        #     sort=data.get("sort"),
        #     start_price=data.get("price_min"),
        #     end_price=data.get("price_max"),
        #     url=config.URL_API_ITEM_LIST,
        #     page=str(api_page)
        # )
        ################################################################################################################
        result = await request_api_fake(page=1)
        #######################################
        response_list = result["result"]["resultList"]

        paginator_page = 1
        key = str(uuid.uuid4().hex)[:6]
        len_list = len(response_list)
        cache_key = CacheKey(key=key, api_page="1").pack()
        print(f"🟩🟩 {cache_key= }")

        cache_data = await redis_get_data_from_cache(cache_key)
        if cache_data is None:
            await redis_set_data_to_cache(key=cache_key, value=response_list)
        item_list_cache = await redis_get_data_from_cache(cache_key)

        paginator = Paginator(array=item_list_cache, page=paginator_page)
        one_item = paginator.get_page()[0]

        callback_kb = ItemCBD(key=key, api_page="1", paginate_page="1").pack()

        print(f"🟩🟩 {cache_key= }")
        print(f"🟩🟥 {callback_kb= }")

        msg = "{0:.50}\n".format(one_item["item"]["title"])
        msg += "👀\t{0}\n".format(one_item["item"]["sales"])
        msg += "💰\t{0} RUB\n".format(one_item["item"]["sku"]["def"]["promotionPrice"])
        msg += "{0}\n\n".format(one_item["item"]["itemUrl"])
        msg += "{0} из {1} [{2}]".format(1, paginator.pages, api_page)
        img = ":".join(["https", one_item["item"]["image"]])

        next_kb = ItemCBD(key=key, api_page=api_page, paginate_page=2).pack()
        last_kb = ItemCBD(key=key, api_page=api_page, paginate_page=paginator.pages).pack()

        kb = await kb_builder(
            size=(1, 2, 1),
            data_list=[
                {"подробно": "item_{0}".format(one_item['item']['itemId'])},
                {"След. ➡️": next_kb},
                {"После. ⏩": last_kb},
                {"🏠 menu": "menu"}
            ]
        )

        photo = types.InputMediaPhoto(media=img, caption=msg, show_caption_above_media=False)
        await call.message.edit_media(media=photo, reply_markup=kb)

        # for msg, img, kb in item_list:
        #     # await asyncio.sleep(0.5)
        #     await call.message.answer_photo(photo=img, caption=msg, reply_markup=kb)
        #
        # msg = 'По запросу\t<b>{0}</b>\n'.format(data['product'])
        # if data.get("price_min") and data.get("price_max"):
        #     msg += 'цена от {0} до {1} руб.\n'.format(
        #         data.get("price_min"),
        #         data.get("price_max")
        #     )
        # msg += 'найдено {0} ед.\ ценовой диапазон: {1} руб.'.format(
        #     len(item_list),
        #     price_range
        # )
        #
        # kb = await kb_builder(
        #     (2,),
        #     [
        #         {'🏠 menu': "menu"},
        #         {"🛒 искать ещё": "search"},
        #         {f"➡️ следующая стр {page}": f"item_list_next_page_{page}"}
        #     ]
        # )
        # await call.message.answer(text=msg, reply_markup=kb, parse_mode='HTML')

    except FreeAPIExceededError as error:
        await call.answer(show_alert=True, text="⚠️ ОШИБКА\n\n{0}".format(error))
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


# @search.message(Command("cache"))
# async def get_key_cache(message: Message, state: FSMContext):
#     await state.set_state(Cache.key)
#     await message.answer('🟥🟨🟩 Введите ключ')
#
#
# @search.message(Cache.key)
# async def get_cache(message: Message, state: FSMContext):
#     await state.update_data(key=message.text)
#
#     ##############################################
#     # _list = await get_routes_from_cache(message.text)
#     _list = await storage.get_cache(message.text)
#     ##############################################
#
#     print(f"\n{type(_list)= }\n")
#     # await message.answer('done')
#     # data = json.loads()
#     # # _path = os.path.join(config.CACHE_PATH, f'{message.text}.json')
#     # #
#     # # with open(_path, 'r') as file:
#     # #     data = json.load(file)
#     #
#     item_list = await deserialize_item_cache(_list)
#     #
#     for msg, img, kb in item_list:
#         await message.answer_photo(photo=img, caption=msg, reply_markup=kb)
