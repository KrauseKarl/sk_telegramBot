import uuid

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    CallbackQuery,
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup
)

from api_aliexpress.deserializers import *
from api_aliexpress.request import *
from api_redis.handlers import *
from api_telegram.statments import *
from api_telegram.callback_data import *
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
        print("*" * 50)

        data = await state.get_data()
        print(f'⬜️🟧{data= }')

        print(f'⬜️🟧 ENDPOINT SEARCH PAGINATION\n⬜️🟧CALLBACK {callback.data}')
        # await callback.answer("🟠 SEARCH PAGINATION")
        key = callback_data.key
        paginate_page = int(callback_data.paginate_page)
        api_page = callback_data.api_page
        cache_key = CacheKey(key=key, api_page=api_page).pack()

        item_list_cache = await redis_get_data_from_cache(cache_key)
        print(f"⬜️🟠{cache_key=  }\n⬜️🟠{api_page=  }\n⬜️🟠{paginate_page=  }\n")
        if int(paginate_page) <= len(item_list_cache):
            print(f"⬜️DATA FROM 🟩 CACHE ")
            paginator = Paginator(array=item_list_cache, page=paginate_page)
            one_item = paginator.get_page()[0]
        else:
            print(f"⬜️DATA FROM 🟥 REQUIEST")
            new_api_page = str(int(api_page) + 1)
            ########################################################################
            data = await state.get_data()

            if config.FAKE_MODE:
                result = await request_api_fake(page=api_page, query=data.get("product"))
            else:
                result = await request_api(
                    query=data.get("product"),
                    sort=data.get("sort"),
                    start_price=data.get("price_min"),
                    end_price=data.get("price_max"),
                    url=config.URL_API_ITEM_LIST,
                    page=str(new_api_page)
                )
            ########################################################################

            item_list_cache = result["result"]["resultList"]
            new_cache_key = CacheKey(key=key, api_page=new_api_page).pack()
            print(f"⬜NEW REQUEST INFO🟥\n⬜️🟥{new_cache_key= }\n⬜️🟥{new_api_page= }\n⬜️🟥{len(item_list_cache)= }")
            paginate_page = 1
            api_page = new_api_page
            cache_key = new_cache_key
            cache_data = await redis_get_data_from_cache(cache_key)
            #
            if cache_data is None:
                await redis_set_data_to_cache(key=cache_key, value=item_list_cache)
            paginator = Paginator(array=item_list_cache, page=paginate_page)
            one_item = paginator.get_page()[0]

        print(
            f"⬜️🟫 {paginate_page} of {len(item_list_cache)}\tPAGE < LEN(LIST) {int(paginate_page) <= len(item_list_cache)}")
        ##########################################################################################
        keyboard_list = []
        first_kb = None
        next_kb = None
        last_kb = None
        prev_kb = None
        ##########################################################################################
        if int(api_page) == 1 and int(paginate_page) == 1:
            print("⬜️⭐🟠🟠🟠__________________ 1й запрос и 1 я страница ")
            # ✅ next = 2
            # ✅ last = paginator.pages
            # ❌ prev None
            # ❌ fist None
            next_kb = ItemCBD(key=key, api_page=api_page, paginate_page=2).pack()
            last_kb = ItemCBD(key=key, api_page=api_page, paginate_page=str(paginator.pages)).pack()
            keyboard_list.extend(
                [
                    {"След. ➡️": next_kb},
                    {"После. ⏩": last_kb}
                ]
            )

        elif int(api_page) > 1 and int(paginate_page) == 1:
            print("⬜️⭐️🟢🟢🟢__________________ Следующий запрос и 1я страница")

            # ✅ next = 2
            # ✅ last = paginator.pages
            # ✅ prev = "itList:cache_key:api_page-1:prev(paginator.pages)" ! after 2nd request to redis by pre_cache_key
            # ❌ fist None
            next_kb = ItemCBD(key=key, api_page=api_page, paginate_page=2).pack()
            last_kb = ItemCBD(key=key, api_page=api_page, paginate_page=str(paginator.pages)).pack()
            prev_paginate_page = len(
                await redis_get_data_from_cache(CacheKey(key=key, api_page=str(int(api_page) - 1)).pack()))
            prev_kb = ItemCBD(key=key, api_page=str(int(api_page) - 1), paginate_page=prev_paginate_page).pack()
            keyboard_list.extend(
                [
                    {"⬅️ Пред.": prev_kb},
                    {"След. ➡️": next_kb},
                    {" После. ⏩": last_kb}
                ]
            )

        elif paginator.pages > int(paginate_page) > 1:
            print("⬜️⭐️ 🟣🟣🟣__________________ следующая страница")
            # ✅ next = paginate_page + 1 if paginate_page + 1 < paginator.pages else paginator.pages
            # ✅ last = paginator.pages
            # ✅ prev = paginate_page - 1  if paginate_page - 1 > 1 else 1
            # ✅ fist = 1

            next_page = str(paginate_page + 1 if paginate_page + 1 < paginator.pages else paginator.pages + 1)
            next_kb = ItemCBD(key=key, api_page=api_page, paginate_page=next_page).pack()
            last_kb = ItemCBD(key=key, api_page=api_page, paginate_page=str(paginator.pages)).pack()
            prev_page = str(paginate_page - 1 if paginate_page - 1 > 1 else 1)
            prev_kb = ItemCBD(key=key, api_page=api_page, paginate_page=prev_page).pack()
            first_kb = ItemCBD(key=key, api_page=api_page, paginate_page=str(1)).pack()
            keyboard_list.extend(
                [

                    {"⬅️ Пред.": prev_kb},
                    {"След. ➡️": next_kb},
                    {"⏪ Первая": first_kb},
                    {"После. ⏩": last_kb}
                ]
            )

        elif int(paginate_page) == paginator.pages:
            print("⬜️⭐️ ⚪️⚪️⚪️__________________ последняя страница ")
            # ✅ next = request to api with api_page + 1
            # ❌ last None
            # ✅ prev paginate_page - 1 if paginate_page - 1 != 0  else 1
            # ✅ fist = 1
            next_kb = ItemCBD(key=key, api_page=api_page, paginate_page=str(paginate_page + 1)).pack()
            prev_page = str(paginate_page - 1 if paginate_page - 1 != 0 else 1)
            prev_kb = ItemCBD(key=key, api_page=api_page, paginate_page=prev_page).pack()
            first_kb = ItemCBD(key=key, api_page=api_page, paginate_page=str(1)).pack()
            keyboard_list.extend(
                [
                    {"⬅️ Пред.": prev_kb},
                    {"След. ➡️": next_kb},
                    {"⏪ Первая": first_kb},
                ]
            )

        else:
            print('⬜️❌❌❌__________________KB ERROR')
        ##########################################################################################
        # builder.button(
        #     text=FavAction.list.value.title(),
        #     callback_data=FavoriteCBD(action=FavAction.list, item_id="123"),
        # )
        keyboard_list.extend(
            [
                {"ℹ️ подробно": "item_{0}".format(one_item['item']['itemId'])},
                {"⭐️ в избранное": FavoriteCBD(action=FavAction.list, item_id=str(one_item['item']['itemId'])).pack()},
                {"🌐": "menu"},
                {"🏠 menu": "menu"}
            ]
        )
        ##########################################################################################

        ##########################################################################################
        mg = ''
        # FIRST
        mg += " ПЕРВАЯ {1}[{0}] ".format(first_kb.split(':')[2],
                                         first_kb.split(':')[3]) if first_kb is not None else "[❌]\t"
        #  PREV
        mg += " ПРЕДЫД {1}[{0}] ".format(prev_kb.split(':')[2],
                                         prev_kb.split(':')[3]) if prev_kb is not None else "[❌]\t"
        #  NEXT
        mg += " СЛКДУЮ {1}[{0}] ".format(next_kb.split(':')[2],
                                         next_kb.split(':')[3]) if next_kb is not None else "[❌]\t"
        # LAST
        mg += " ПОСЛЕД {1}[{0}] ".format(last_kb.split(':')[2],
                                         last_kb.split(':')[3]) if last_kb is not None else "[❌]\t"
        print('⬜️ KEYBOARD {}'.format(mg))
        ##########################################################################################

        print("*" * 50)

        # todo message builder
        msg = "{0:.50}\n".format(one_item["item"]["title"])
        msg += "👀\t{0}\n".format(one_item["item"]["sales"])
        msg += "💰\t{0} RUB\n".format(one_item["item"]["sku"]["def"]["promotionPrice"])
        msg += "{0}\n\n".format(one_item["item"]["itemUrl"])
        msg += "{0} из {1} стр. {2}".format(paginate_page, paginator.pages, api_page)
        img = ":".join(["https", one_item["item"]["image"]])
        photo = types.InputMediaPhoto(media=img, caption=msg, show_caption_above_media=False)
        # todo message builder

        kb = await builder_kb(keyboard_list, (2,))

        await callback.message.edit_media(media=photo, reply_markup=kb)

    except CustomError as error:
        # msg, photo = await get_error_answer_photo(error)
        # await callback.message.answer_photo(
        #     photo=photo,
        #     caption=msg,
        #     reply_markup=await error_kb()
        # )
        await callback.answer(text=str(error), show_alert=True)


@search.callback_query(ItemFSM.sort)
async def search_result(call: CallbackQuery, state: FSMContext) -> None:
    """
    
    :param cache_state:
    :param call:
    :param state: 
    :return: 
    """
    print('️⬛️🟨 ENDPOINT SEARCH RESULT')

    try:
        await state.update_data(sort=call.data)

        api_page = 1
        ################################################################################################################
        data = await state.get_data()

        await state.set_state(CacheFSM.product)
        await state.update_data(product=data.get("product"))

        await state.set_state(CacheFSM.price_min)
        await state.update_data(price_min=data.get("price_min"))

        await state.set_state(CacheFSM.price_max)
        await state.update_data(price_max=data.get("price_max"))

        await state.set_state(CacheFSM.qnt)
        await state.update_data(qnt=data.get("qnt"))

        await state.set_state(CacheFSM.sort)
        await state.update_data(sort=data.get("sort"))

        if config.FAKE_MODE:
            result = await request_api_fake(page=1, query=data.get("product"))
        else:
            result = await request_api(
                query=data.get("product"),
                sort=data.get("sort"),
                start_price=data.get("price_min"),
                end_price=data.get("price_max"),
                url=config.URL_API_ITEM_LIST,
                page=str(api_page)
            )

        ################################################################################################################

        response_list = result["result"]["resultList"]

        paginator_page = 1
        key = str(uuid.uuid4().hex)[:6]
        cache_key = CacheKey(key=key, api_page="1").pack()
        cache_data = await redis_get_data_from_cache(cache_key)
        if cache_data is None:
            await redis_set_data_to_cache(key=cache_key, value=response_list)
        item_list_cache = await redis_get_data_from_cache(cache_key)

        paginator = Paginator(array=item_list_cache, page=paginator_page)
        one_item = paginator.get_page()[0]

        callback_kb = ItemCBD(key=key, api_page="1", paginate_page="1").pack()

        sort_price_set = set(sorted([item["item"]["sku"]["def"]["promotionPrice"] for item in item_list_cache]))
        price_range_list = '{0} - {1}'.format(min(sort_price_set), max(sort_price_set))
        print(f"⬛️🟨 {data.items()= }")
        print(f"⬛️🟨 {cache_key= }")
        print(f"⬛️🟨 {callback_kb= }")
        print(f"⬛️🟨 {price_range_list= }")
        msg = "{0:.50}\n".format(one_item["item"]["title"])
        msg += "👀\t{0}\n".format(one_item["item"]["sales"])
        msg += "💰\t{0} RUB\n".format(one_item["item"]["sku"]["def"]["promotionPrice"])
        msg += "{0}\n\n".format(one_item["item"]["itemUrl"])
        msg += "{0} из {1} стр. {2}".format(1, paginator.pages, api_page)
        img = ":".join(["https", one_item["item"]["image"]])

        next_kb = ItemCBD(key=key, api_page=api_page, paginate_page=2).pack()
        last_kb = ItemCBD(key=key, api_page=api_page, paginate_page=paginator.pages).pack()

        kb = await kb_builder(
            size=(2,),
            data_list=[
                {"След. ➡️": next_kb},
                {"После. ⏩": last_kb},
                {"ℹ️ подробно": "item_{0}".format(one_item['item']['itemId'])},
                {"🏠 menu": "menu"}
            ]
        )

        await orm_make_record_request(
            HistoryModel(
                user=call.from_user.id,
                command='search',
                price_range=''.format(data.get('price_min'), data.get('price_max')),
                price_min=data.get('price_min'),
                price_max=data.get('price_max'),
                search_name=data['product'],
                sort=config.SORT_DICT[data['sort']]
            ).model_dump())  # todo make orm func for orm.py
        await state.clear()
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
