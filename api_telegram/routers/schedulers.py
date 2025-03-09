from aiogram import Router, F, types
from aiogram.filters import Command

from api_telegram.crud.scheduler import remove_job, create_item_search
from utils.media import *
import matplotlib.pyplot as plt

scheduler = Router()


@scheduler.callback_query(F.data.startswith("item_search"))
async def add_search(callback: types.CallbackQuery):
    # try:
        item_id = callback.data.split(":")[1]
        await create_item_search(item_id, callback.from_user.id)
        await callback.answer(
            f"Поисковый запрос '{item_id}' добавлен.",
            show_alert=True
        )
    # except Exception as error:
    #     print('error = ', error)
    #     await callback.answer(str(error), show_alert=True)


# Команда /list_searches
@scheduler.callback_query(F.data.startswith("list_searches"))
async def list_searches(callback: types.CallbackQuery):
    try:
        searches = ItemSearch.select()
        if not searches:
            await callback.message.answer("Поисковые запросы отсутствуют.")
            return

        response = "Список поисковых запросов:\n"
        for search in searches:
            response += f"- {search.title} (ID: {search.product_id})\n"
        await callback.message.answer(response)
    except Exception as error:
        await callback.answer(str(error))

# Команда /delete_search
@scheduler.message(Command("delete_search"))
async def delete_search(message: types.Message):
    # Пример: Получаем ID поискового запроса из аргументов команды
    args = message.text.split()
    if len(args) < 2:
        await message.answer("Укажите ID поискового запроса: /delete_search <item_search_id>")
        return

    try:
        item_search_id = int(args[1])
        item_search = ItemSearch.get_by_id(item_search_id)
    except (ValueError, ItemSearch.DoesNotExist):
        await message.answer("Неверный ID поискового запроса.")
        return

    # Удаляем задачу из планировщика
    remove_job(item_search.id)

    # Удаляем поисковый запрос из базы данных
    item_search.delete_instance()
    await message.answer(f"Поисковый запрос '{item_search.name}' (ID: {item_search.id}) удален.")


# Команда /graph
# Команда /graph
@scheduler.message(Command("graph"))
async def send_graph(message: types.Message):
    # Пример: Получаем ID поискового запроса из аргументов команды
    args = message.text.split()
    if len(args) < 2:
        await message.answer("Укажите ID поискового запроса: /graph <item_search_id>")
        return

    try:
        item_search_id = int(args[1])
        item_search = ItemSearch.get_by_id(item_search_id)
    except (ValueError, ItemSearch.DoesNotExist):
        await message.answer("Неверный ID поискового запроса.")
        return

    # Получаем данные, связанные с поисковым запросом
    entries = DataEntry.select().where(DataEntry.item_search == item_search).order_by(DataEntry.timestamp)

    if not entries:
        await message.answer("Данные отсутствуют.")
        return

    # Подготовка данных для графика
    timestamps = [entry.timestamp for entry in entries]
    values = [entry.value for entry in entries]

    # Построение графика
    plt.figure(figsize=(10, 5))
    plt.plot(timestamps, values, marker="o")
    plt.title(f"График изменения данных для '{item_search.name}'")
    plt.xlabel("Время")
    plt.ylabel("Значение")
    plt.grid(True)
    plt.savefig("graph.png")

    # Отправка графика пользователю
    await message.answer_photo(FSInputFile("graph.png"))
