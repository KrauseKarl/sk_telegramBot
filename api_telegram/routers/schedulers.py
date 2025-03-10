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
        searched_items = ItemSearch.select().where(ItemSearch.user == callback.from_user.id)
        if not searched_items:
            await callback.message.answer("Поисковые запросы отсутствуют.")
            return

        msg = "Список поисковых запросов:\n"
        for item_search in searched_items:
            msg += "{0:.50} (ID: {1})\n".format(item_search.title, item_search.product_id)
            photo = InputMediaPhoto(media=item_search.image, caption=msg)
            await callback.message.edit_media(media=photo)
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
    print(message.text)
    args = message.text.split()
    if len(args) < 2:
        await message.answer("Укажите ID поискового запроса: /graph <item_search_id>")
        return

    try:
        item_search_id = int(args[1])
        item_search = ItemSearch.select().where(ItemSearch.uid == item_search_id).get_or_none()
        if item_search is None:
            raise ValueError
    except (ValueError, ItemSearch.DoesNotExist):
        await message.answer("Неверный ID поискового запроса.")
        return

    # Получаем данные, связанные с поисковым запросом
    entries = DataEntry.select().where(DataEntry.item_search == item_search).order_by(DataEntry.date)

    if not entries:
        await message.answer("Данные отсутствуют.")
        return

    # Подготовка данных для графика
    timestamps = [entry.date for entry in entries]
    values = [entry.value for entry in entries]

    # todo create def graf_bar_maker()
    plt.style.use('dark_background')
    plt.figure(figsize=(12, 9), dpi=120)
    plt.plot(timestamps, values, color='orange', marker="o", markersize=20, linewidth=5)

    for x, y in zip(timestamps, values):
        plt.text(x, y, f'{y}', fontsize=18, ha='center', va='bottom', color='white', bbox=dict(facecolor='red', alpha=0.8))
    plt.title("График изменения данных для '{0:.50}'".format(item_search.title))
    plt.xlabel("Время")
    plt.ylabel("Цена")
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.savefig("graph.png")

    # Отправка графика пользователю
    await message.answer_photo(FSInputFile("graph.png"))
