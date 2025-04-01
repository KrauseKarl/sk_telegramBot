import locale

from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.types import Message

from api_telegram.callback_data import Navigation
from api_telegram.crud.scheduler import remove_job, create_item_search, MonitorManager
from api_telegram import BasePaginationBtn, MonitorAction, MonitorCBD, HistoryCBD, HistoryAction
from database import orm_get_monitoring_list, ItemSearch, DataEntry
from utils.media import *
import matplotlib.pyplot as plt

monitor = Router()


# @scheduler.callback_query(F.data.startswith("item_search"))
@monitor.callback_query(MonitorCBD.filter(F.action == MonitorAction.add))
async def add_search(callback: types.CallbackQuery, callback_data: MonitorCBD):
    try:
        item_id = int(callback_data.item_id)
        await create_item_search(item_id, callback.from_user.id)
        await callback.answer(
            f"Поисковый запрос '{item_id}' добавлен.",
            show_alert=True
        )
    except Exception as error:
        await callback.answer(str(error), show_alert=True)


@monitor.message(Command("monitor"))
@monitor.callback_query(MonitorCBD.filter(F.action == MonitorAction.paginate))
@monitor.callback_query(MonitorCBD.filter(F.action == MonitorAction.list))
@monitor.callback_query(MonitorCBD.filter(F.action == MonitorAction.back))
async def list_searches(callback: types.CallbackQuery, callback_data: MonitorCBD):
    try:
        searched_items = await orm_get_monitoring_list(callback.from_user.id)
        if not searched_items:
            await callback.message.answer("Поисковые запросы отсутствуют.")
            return
        if callback_data is None:
            callback_data = HistoryCBD(
                action=HistoryAction.first,
                navigate=Navigation.first
            )
        manager = MonitorManager(callback_data, callback.from_user.id)
        if isinstance(callback, Message):
            await callback.answer_photo(
                photo=await manager.get_photo(),
                caption=await manager.get_msg(),
                reply_markup=await manager.get_keyboard()
            )
        else:
            await callback.message.edit_media(
                media=await manager.get_media(),
                reply_markup=await manager.get_keyboard()
            )
        # msg, photo, kb = await get_searched_items_list(callback, callback_data)
        # await callback.message.edit_media(media=photo, reply_markup=kb.create_kb())
    except Exception as error:
        await callback.answer(str(error)[:100])


# Команда /delete_search
@monitor.message(Command("delete_search"))
@monitor.callback_query(MonitorCBD.filter(F.action == MonitorAction.delete))
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


# TODO refactoring graph
@monitor.callback_query(MonitorCBD.filter(F.action == MonitorAction.graph))
async def send_graph(callback: types.CallbackQuery, callback_data: MonitorCBD):
    # Пример: Получаем ID поискового запроса из аргументов команды
    try:
        # print(message.text)
        # args = callback_data.
        # if len(args) < 2:
        #     await message.answer("Укажите ID поискового запроса: /graph <item_search_id>")
        #     return
        try:
            # item_search_id = int(args[1])
            item_search_id = callback_data.item_id
            item_search = ItemSearch.select().where(ItemSearch.product_id == item_search_id).get_or_none()
            if item_search is None:
                raise ValueError
        except (ValueError, ItemSearch.DoesNotExist):
            await callback.message.answer("Неверный ID поискового запроса.")
            return

        # Получаем данные, связанные с поисковым запросом
        entries = DataEntry.select().where(DataEntry.item_search == item_search).order_by(DataEntry.date)

        if not entries:
            await callback.message.answer("Данные отсутствуют.")
            return

        locale.setlocale(category=locale.LC_ALL, locale="Russian")
        # todo create def graf_bar_maker()
        values = [entry.value for entry in entries]
        timestamps = [entry.date.strftime('%b %d') for entry in entries]
        plt.style.use('dark_background')
        plt.figure(figsize=(20, 9), dpi=300)
        plt.ylim(min(values) - min(values) * 0.25, max(values) + min(values) * 0.25)
        plt.plot(timestamps, values, color='grey', marker="o", markersize=20, linewidth=5)

        # todo func `if min value is not the only`
        def last_elem(x_axis, y_axis, sort_value):
            result_dict = dict()
            for x, y in zip(x_axis, y_axis):
                if sort_value == 'min':
                    if min(values) == y:
                        result_dict[x] = y
                if sort_value == 'max':
                    if max(values) == y:
                        result_dict[x] = y
            last_item = sorted(result_dict.items())[-1]
            return last_item[0], last_item[1]

        # todo func `if min value is not the only`
        max_time_value, max_value = last_elem(timestamps, values, "max")
        min_time_value, min_value = last_elem(timestamps, values, "min")
        for x, y in zip(timestamps, values):
            max_time_value, max_value = last_elem(timestamps, values, "max")
            min_time_value, min_value = last_elem(timestamps, values, "min")
            if x == max_time_value:
                plt.text(x, y, f'{y}', fontsize=20, ha='center', va='bottom', color='white',
                         bbox=dict(facecolor='red', alpha=0.8))
            if x == min_time_value:
                plt.text(x, y, f'{y}', fontsize=20, ha='center', va='bottom', color='white',
                         bbox=dict(facecolor='green', alpha=0.8))
            if values[-1] == y:
                plt.text(x, y, f'{y}', fontsize=20, ha='center', va='bottom', color='white',
                         bbox=dict(facecolor='orange', alpha=0.8))

        plt.text(0.99, 0.99,  # Координаты (x, y) в долях от размеров графика (0.95 — почти в правом верхнем углу)
                 f'Максимум: {max(values)}',  # Текст аннотации
                 horizontalalignment='right',  # Выравнивание текста по правому краю
                 verticalalignment='top',  # Выравнивание текста по верхнему краю
                 transform=plt.gca().transAxes,  # Использование относительных координат (доли графика)
                 fontsize=25, color='white', bbox=dict(facecolor='red', alpha=0.8))  # Настройки шрифта и цвета
        plt.text(0.99, 0.90,  # Координаты (x, y) в долях от размеров графика (0.95 — почти в правом верхнем углу)
                 f'Минимум: {min(values)}',  # Текст аннотации
                 horizontalalignment='right',  # Выравнивание текста по правому краю
                 verticalalignment='top',  # Выравнивание текста по верхнему краю
                 transform=plt.gca().transAxes,  # Использование относительных координат (доли графика)
                 fontsize=25, color='white', bbox=dict(facecolor='green', alpha=0.8))
        plt.title(
            "График изменения цены для '{0:.25}'".format(item_search.title),
            fontdict=dict(color='white', fontsize=22)
        )
        plt.xlabel("Период", fontdict=dict(color='white', fontsize=25))
        plt.ylabel("Цена", fontdict=dict(color='white', fontsize=25))
        plt.grid(axis='y', visible=True, linestyle='-', alpha=0.5)
        plt.grid(axis='x', visible=True, linestyle='-', alpha=0.3)
        plt.xticks(timestamps)
        plt.savefig("graph.png")

        msg = f"\r\n📈 max цена = {max(values)}\t({max_time_value})\r\n" \
              f"📉 min цена = {min(values)}\t({min_time_value})\r\n" \
              f"📅 текущая цена = {values[-1]}\t({timestamps[-1]})\r\n"
        photo = InputMediaPhoto(media=FSInputFile("graph.png"), caption=msg)
        kb = BasePaginationBtn()
        print(callback_data)
        kb_data = MonitorCBD(
            action=MonitorAction.list,
            navigate=callback_data.navigate,
            monitor_id=callback_data.monitor_id,
            item_id=callback_data.item_id,
            page=callback_data.page
        ).pack()
        kb.add_button(kb.btn_data('back', kb_data)).add_markup(1)
        # kb.add_button(kb.btn_text('li')).add_markup(1)
        print(kb.get_kb())
        await callback.message.edit_media(media=photo, reply_markup=kb.create_kb())
    except Exception as error:
        print(error)
        await callback.message.answer(str(error))
