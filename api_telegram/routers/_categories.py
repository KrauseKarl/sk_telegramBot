from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command, or_f
from aiogram.fsm.context import FSMContext
from aiogram.types import (CallbackQuery, InlineKeyboardButton, KeyboardButton,
                           Message, ReplyKeyboardMarkup)
from aiogram.utils.keyboard import InlineKeyboardBuilder

from api_aliexpress.request import *
from api_telegram.statments import *
from database.exceptions import CustomError
from database.orm import orm_make_record_request
from utils.media import *
from utils.message_info import *

category = Router()


# CATEGORY  ###########################################################################################################
@category.message(Command("category"))
async def search_category_message(
        message: Message, state: FSMContext
) -> None:
    """

    :param message:
    :param state:
    :return:
    """
    try:
        await state.set_state(CategoryFSM.name)
        await message.edit_media(media=await get_input_media_hero_image(
            "category",
            "🛍️ Введите название категории?"
        ))
    except TelegramBadRequest:
        await state.set_state(CategoryFSM.name)
        await message.answer_photo(
            photo=await get_fs_input_hero_image("category", ),
            caption="🛍️ Введите название категории?"
        )
    except CustomError as error:
        await message.edit_media(
            media=await get_error_answer_media(error),
            reply_markup=await qnt_kb()
        )


@category.callback_query(F.data.startswith("category"))
async def search_category_callback(
        callback: CallbackQuery, state: FSMContext
) -> None:
    """

    :param callback:
    :param state:
    :return:
    """
    await state.set_state(CategoryFSM.name)
    await callback.message.edit_media(
        media=await get_input_media_hero_image(
            "category",
            "Введите название товара или категории?"
        ))


@category.message(CategoryFSM.name)
async def search_category_name(
        message: Message, state: FSMContext
) -> None:
    """

    :param message:
    :param state:
    :return:
    """
    await state.update_data(name=message.text)
    await state.set_state(CategoryFSM.cat_id)

    await message.answer("⌛ searching <u>{0}</u>".format(message.text))

    result = await request_api(url=config.URL_API_CATEGORY)

    item_list = result["result"]["resultList"]
    await state.clear()
    # kb = InlineKeyboardBuilder()
    if len(item_list) > 0:

        count = 0
        result = []
        for cat in item_list:
            n = cat.get("name")
            uid = str(cat.get("id"))
            if message.text.lower() in n.lower():
                count += 1
                result.append(
                    {
                        '⭕️ {0} [{1}]'.format(n, uid):  "cat_id_{}".format(uid)
                    }
                )
                print(f'✅{n}')

            for sub_cat in cat.get("list"):
                sub_cat_name = sub_cat.get("name")
                if sub_cat_name:
                    if message.text.lower() in sub_cat_name.lower():
                        count += 1
                        sn = sub_cat.get("name")
                        sid = str(sub_cat.get("id"))
                        result.append(
                            {
                                '⭕️ {0} [{1:.20}]'.format(sn, n): "cat_id_{}".format(sid)
                            }
                        )
                        print(f'✅✅✅ {sn}')
        if len(result) == 0:
            mgs = ("⚠️По вашему запросу ничего не найдено."
                   "\nПопробуйте сформулировать запрос иначе.")
            await message.answer(mgs, reply_markup=await menu_kb())
        kb = await kb_builder((1, ), result)

        # result_list = category_info(
        #     items=item,
        #     query=message.text
        # )
        # await message.answer(f"cat - {msg=}|{cat_title=}{number=}|{count=}|")
        # data = "cat_id_{}".format(number)
        # if len(msg) > 2:
        #     button = InlineKeyboardButton(
        #         text="⭕️ {0}".format(cat_title),
        #         data=data
        #     )
        #     kb.add(button)

        await message.answer(
            "по запросу <u>{0}</u>\nнайдены следующие категории [{1}]".format(
                message.text, count
            ),
            reply_markup=kb
        )
    else:
        mgs = ("⚠️По вашему запросу ничего не найдено."
               "\nПопробуйте сформулировать запрос иначе.")
        await message.answer(mgs, reply_markup=await menu_kb())


@category.callback_query(
    or_f(CategoryFSM.cat_id, F.data.startswith("cat_id")
         )
)
async def search_category_product_name(
        callback: CallbackQuery, state: FSMContext
) -> None:
    """

    :param callback:
    :param state:
    :return:
    """
    category_id = int(str(callback.data).split('_')[2])
    await state.update_data(cat_id=category_id)
    await state.set_state(CategoryFSM.product)
    await callback.message.answer_photo(
        photo=await get_fs_input_hero_image("category"),
        caption="🛍️ Введите название товара."
    )


@category.message(CategoryFSM.product)
async def search_category_sort(message: Message, state: FSMContext) -> None:
    """

    :param message:
    :param state:
    :return:
    """
    await state.update_data(product=message.text)
    await state.set_state(CategoryFSM.sort)
    await message.answer_photo(
        photo=await get_fs_input_hero_image("category"),
        caption="Как отсортировать результат?",
        reply_markup=await sort_kb()
    )


@category.callback_query(CategoryFSM.sort, F.data.in_(SORT_SET))
async def search_category_qnt(
        callback: CallbackQuery, state: FSMContext
) -> None:
    """

    :param callback:
    :param state:
    :return:
    """
    await state.update_data(sort=callback.data)
    await state.set_state(CategoryFSM.qnt)
    await callback.message.edit_media(
        media=await get_input_media_hero_image(
            "category",
            "сколько единиц товара вывести?"),
        reply_markup=await qnt_kb()
    )


@category.callback_query(CategoryFSM.qnt, F.data.in_(QNT))
async def search_category_result(
        callback: CallbackQuery, state: FSMContext
) -> None:
    """

    :param callback:
    :param state:
    :return:
    """
    await state.update_data(qnt=callback.data)
    data = await state.get_data()
    print(f"{data= }")
    search_data = dict()
    price_range_list = []
    try:
        await callback.answer("⌛ searching {0}".format(data['product']))
        result = await request_api(
            url=config.URL_API_ITEM_LIST,
            query=data.get("product"),
            sort=data.get("sort"),
            cat_id=data.get("cat_id")
        )
        print(result)
        try:
            print("{0}\n❌ лимит бесплатных API превышен".format(result["message"]))
        except KeyError:
            pass
        ranges = int(data["qnt"])  # todo make deserializer
        item_list = result["result"]["resultList"][:ranges]
        currency = result["result"]["settings"]["currency"]

        for item in item_list:
            msg, img = card_info(item, currency)
            item_id = item["item"]["itemId"]
            kb = await builder_kb(
                data=[
                    {"👀 подробно": "{0}_{1}".format("item", item_id)},
                    {"⭐️ в избранное": "{0}_{1}".format("fav_pre_add", item_id)}
                ],
                size=(2,)
            )
            price = item["item"]["sku"]["def"]["promotionPrice"]
            price_range_list.append(price)
            await callback.message.answer_photo(
                photo=img, caption=msg, reply_markup=kb)
        await callback.message.answer(
            text='По запросу {0}\n найдено {1}\nв ценовой диапазоне {2}'.format(
                data['product'],
                len(item_list),
                get_price_range(price_range_list)
            ),
            reply_markup=await menu_kb()
        )

        await orm_make_record_request(
            HistoryModel(
                user=callback.from_user.id,
                command='search',
                price_range=get_price_range(price_range_list),
                result_qnt=int(ranges),
                search_name=data['product'],
            ).model_dump())  # todo make orm func for orm.py

        await state.clear()
    except (CustomError, KeyError) as err:
        await callback.message.answer(
            "⚠️ Ошибка\n{0}".format(str(err)),
            reply_markup=await menu_kb()
        )
