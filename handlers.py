from aiogram import Router, types, F
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart, or_f
from aiogram.exceptions import AiogramError
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from config import SORT, settings
from statments import Form, CategoryForm
from utils import (
    card_info,
    category_info,
    request_handler,
    request_detail,
    detail_info,
    detail_img,
    request_detail_2,
    detail_info_2, detail_color_img
)
from keyboards import sort_keyboard, item_kb

router = Router()


@router.message(CommandStart())
async def start_command(message: types.Message) -> None:
    await message.answer("Привет! Я виртуальный помощник 😀")


@router.message(Command("search"))
async def request_item_name(message: Message, state: FSMContext) -> None:
    await state.set_state(Form.product)
    await message.answer(
        "🛍️ Введите название товара."
    )


@router.message(Form.product)
async def item_search_sort(message: Message, state: FSMContext) -> None:
    await state.update_data(product=message.text)
    await state.set_state(Form.sort)
    await message.answer(
        "Как отсортировать результат?", reply_markup=sort_keyboard
    )
    # await message.answer(
    #     "Как отсортировать результат.\nпо умолчанию [default],\n"
    # )
    # await message.answer(
    #     "⬇️ по убыванию [priceDesc],\n⬆️ по возрастанию [priceDesc],\n"
    # )
    # await message.answer(
    #     "💰 по продажам [salesDesc]"
    # )


# def get_inline_kb():
#     inline_kb_list = [
#         [InlineKeyboardButton(text="Генерировать пользователя", callback_data='get_person')],
#         [InlineKeyboardButton(text="На главную", callback_data='back_home')]
#     ]
#     return InlineKeyboardMarkup(inline_keyboard=inline_kb_list)


@router.callback_query(Form.sort, F.data.in_({'default', 'priceDesc', 'priceAsc', 'salesDesc'}))
async def item_search_qnt(call: CallbackQuery, state: FSMContext) -> None:
    print('+', call.data)
    await state.update_data(sort=call.data)
    await state.set_state(Form.qnt)
    await call.message.answer("сколько единиц товара вывести")


# @router.callback_query()
# async def sort(callback: CallbackQuery):
#     print("* data", callback.data)
#     if callback.data == "priceDesc":
#         return await callback.answer("priceDesc")
#     elif callback.data == "priceAsc":
#         return await callback.answer("priceAsc")
#     elif callback.data == "salesDesc":
#         return await callback.answer("salesDesc")
#     else:
#         return await callback.answer("default")


# @router.message(Form.sort, F.text)
# async def item_search_qnt(message: Message, state: FSMContext) -> None:
#     print(message.text)
#     await state.update_data(sort=message.text)
#     await state.set_state(Form.qnt)
#     await message.answer(
#         "сколько единиц товара вывести"
#     )


@router.message(Form.qnt)
async def item_search_result(message: Message, state: FSMContext) -> None:
    await state.update_data(qnt=message.text)
    data = await state.get_data()
    try:
        q = data['product']
        sort = data['sort']
        ranges = int(data['qnt'])
        print(f"⌛ searching ... 🔍{q}...")
        await message.answer(f"⌛ searching ... 🔍{q}...")
        result = await request_handler(
            q=q,
            sort=sort,
            current_url="item_search_2"
        )
        try:
            print(result['message'])
            print("❌ лимит бесплатных API превышен")
        except KeyError:
            pass
        item_list = result["result"]["resultList"][:ranges]
        currency = result["result"]["settings"]["currency"]
        for i in item_list:
            msg = card_info(i, currency)
            i_kb = await item_kb(i["item"]['itemId'])
            await message.answer(msg, reply_markup=i_kb)
        await state.clear()
    except AiogramError as err:
        await message.answer('⚠️ Я тебя не понимаю, напиши.')


@router.callback_query(F.data.startswith('item'))
async def item_detail(call: CallbackQuery, state: FSMContext) -> None:
    print('+', call.data)
    item_id = str(call.data).split('_')[1]
    response = await request_detail_2(item_id)
    try:
        msg = detail_info_2(response)
        await call.message.answer(msg)

        img_color = detail_color_img(response)
        print(img_color)
        print(len(img_color))

        def separate_img_by_ten(obj: list, num: int = 9):
            for i in range(0, len(obj), num):
                yield obj[i:i + num]
        image_color_list = list(separate_img_by_ten(img_color, 9))
        await call.message.answer("Количество цветов {0}".format(len(img_color)))
        for img in image_color_list:
            color_images = [types.InputMediaPhoto(media=i) for i in img]
            await call.message.answer_media_group(color_images)

        images = detail_img(response)
        image_color_list = list(separate_img_by_ten(images, 9))
        await call.message.answer("Все иллюстрации")
        for img in image_color_list:
            color_images = [types.InputMediaPhoto(media=i) for i in img]
            await call.message.answer_media_group(color_images)
    except AiogramError as err:
        err = response['result']['status']['data']
        msg = response['result']['status']['msg']['data-error']
        await call.message.answer(f'⚠️ Произошла ошибка{err}.')
        await call.message.answer(msg)


@router.message(Command("category"))
async def category_search(message: Message, state: FSMContext) -> None:
    await state.set_state(CategoryForm.name)
    await message.answer(
        "🛍️ Введите название товара или категории."
    )
    print("⌛ searching...")


@router.message(CategoryForm.name)
async def request_sorting(message: Message, state: FSMContext) -> None:
    q = message.text
    await state.update_data(name=q)
    await message.answer("⌛ searching.")
    result = await request_handler(current_url="category_list_1")
    item_list = result["result"]["resultList"]
    await state.clear()
    for i in item_list:
        msg = category_info(i, q)
        if msg is not None:
            await message.answer(**msg.as_kwargs())
