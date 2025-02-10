from aiogram import F, Router
from aiogram.exceptions import AiogramError, TelegramBadRequest
from aiogram.filters import or_f, Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from database.exceptions import CustomError
from keyboards import *
from request import *
from statments import *
from utils import *

category = Router()


# CATEGORY  ###########################################################################################################
@category.message(Command("category"))
async def search_category_message(
        message: Message, state: FSMContext
) -> None:
    try:
        await state.set_state(CategoryForm.name)
        await message.edit_media(media=await get_input_media_hero_image(
            "category",
            "🛍️ Введите название категории?"
        ))
    except TelegramBadRequest:
        await state.set_state(CategoryForm.name)
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
    await state.set_state(CategoryForm.name)
    await callback.message.edit_media(media=await get_input_media_hero_image(
        "category",
        "Введите название товара или категории?"
    ))


@category.message(CategoryForm.name)
async def search_category_name(message: Message, state: FSMContext) -> None:
    await state.update_data(name=message.text)
    await state.set_state(CategoryForm.cat_id)
    await message.answer("⌛ searching <u>{0}</u>".format(message.text), parse_mode="HTML")
    result = await request_item_list(url="category_list_1")
    item_list = result["result"]["resultList"]
    await state.clear()
    kb = InlineKeyboardBuilder()
    if len(item_list) > 0:

        count = 0
        for item in item_list:
            msg, cat_title, number, count = category_info(items=item, query=message.text)
            # print(f"{msg=}|{cat_title=}{number=}|{count=}|")
            data = "cat_id_{}".format(number)
            if len(msg) > 2:
                button = InlineKeyboardButton(text="⭕️ {0}".format(cat_title), callback_data=data)
                kb.add(button)
        await message.answer(
            "по запросу <u>{0}</u>\nнайдены следующие категории [{1}]".format(message.text, count),
            reply_markup=kb.adjust(*(2, 1, 1, 2)).as_markup()
        )
    else:
        mgs = "⚠️По вашему запросу ничего не найдено.\nПопробуйте сформулировать запрос иначе."
        await message.answer(mgs, reply_markup=await menu_kb())


@category.callback_query(or_f(CategoryForm.cat_id, F.data.startswith("cat_id")))
async def search_category_product_name(callback: CallbackQuery, state: FSMContext) -> None:
    category_id = int(str(callback.data).split('_')[2])
    await state.update_data(cat_id=category_id)
    await state.set_state(CategoryForm.product)
    await callback.message.answer_photo(
        photo=await get_fs_input_hero_image("category"),
        caption="🛍️ Введите название товара."
    )


@category.message(CategoryForm.product)
async def search_category_sort(message: Message, state: FSMContext) -> None:
    await state.update_data(product=message.text)
    await state.set_state(CategoryForm.sort)
    await message.answer_photo(
        photo=await get_fs_input_hero_image("category"),
        caption="Как отсортировать результат?",
        reply_markup=await sort_kb()
    )


@category.callback_query(CategoryForm.sort, F.data.in_(SORT_SET))
async def search_category_qnt(callback: CallbackQuery, state: FSMContext) -> None:
    await state.update_data(sort=callback.data)
    await state.set_state(CategoryForm.qnt)
    await callback.message.edit_media(
        media=await get_input_media_hero_image(
            "category",
            "сколько единиц товара вывести?"),
        reply_markup=await qnt_kb()
    )


@category.callback_query(CategoryForm.qnt, F.data.in_(QNT))
async def search_category_result(callback: CallbackQuery, state: FSMContext) -> None:
    await state.update_data(qnt=callback.data)
    data = await state.get_data()
    search_data = dict()
    price_range_list = []
    try:
        await callback.answer("⌛ searching {0}".format(data['product']))
        result = await request_item_list(
            q=data["product"],
            sort=data["sort"],
            url="item_search_2",
            cat_id=data["cat_id"],
        )
        try:
            print("{0}\n❌ лимит бесплатных API превышен".format(result["message"]))
        except KeyError:
            pass
        ranges = int(data["qnt"])  # todo make deserializer
        item_list = result["result"]["resultList"][:ranges]
        currency = result["result"]["settings"]["currency"]

        for item in item_list:
            msg, img = card_info(item, currency)
            kb = await item_kb(item["item"]["itemId"])
            price = item["item"]["sku"]["def"]["promotionPrice"]
            price_range_list.append(price)
            await callback.message.answer_photo(
                photo=img, caption=msg, reply_markup=kb, parse_mode="HTML")

        search_data['user'] = callback.from_user.id
        search_data['command'] = 'search'
        search_data["price_range"] = get_price_range(price_range_list)
        search_data['result_qnt'] = int(ranges)
        search_data['search_name'] = data['product']
        History().create(**search_data).save()  # todo make orm func for orm.py

        await state.clear()
    except CustomError as err:
        await callback.message.answer("⚠️ Ошибка\n{0}".format(str(err)))
