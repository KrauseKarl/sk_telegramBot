from aiogram import Router, types
from aiogram.filters import Command, CommandStart
from aiogram.exceptions import AiogramError
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from config import SORT, settings
from statments import Form
from utils import card_info, category_info, request_handler

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
async def request_sorting(message: Message, state: FSMContext) -> None:
    await state.update_data(product=message.text)
    await state.set_state(Form.sort)
    await message.answer(
        "Как отсортировать результат.\nпо умолчанию [default],\n"
    )
    await message.answer(
        "⬇️ по убыванию [priceDesc],\n⬆️ по возрастанию [priceDesc],\n"
    )
    await message.answer(
        "💰 по продажам [salesDesc]"
    )


@router.message(Form.sort)
async def request_pagination(message: Message, state: FSMContext) -> None:
    await state.update_data(sort=message.text)
    await state.set_state(Form.qnt)
    await message.answer(
        "сколько единиц товара вывести"
    )


@router.message(Form.qnt)
async def item_search(message: Message, state: FSMContext) -> None:
    await state.update_data(qnt=message.text)
    data = await state.get_data()
    print(data)
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
        item_list = result["result"]["resultList"][:ranges]
        currency = result["result"]["settings"]["currency"]
        for i in item_list:
            msg = card_info(i, currency)
            await message.answer(msg)
        await state.clear()
    except AiogramError as err:
        await message.answer('⚠️ Я тебя не понимаю, напиши.')


@router.message(Command("category"))
async def category_search(message) -> None:
    print("⌛ searching...")
    await message.answer("⌛ searching.")
    result = await request_handler(current_url="category_list_1")
    item_list = result["result"]["resultList"]
    for i in item_list:
        msg = category_info(i)
        await message.answer(msg)
