import locale

from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, InputMediaPhoto, FSInputFile

from api_telegram.callback_data import Navigation
from api_telegram.crud import (
    MonitorListManager,
    MonitorDeleteManager,
    MonitorAddManager,
    DefineTargetManger
)
from api_telegram import BasePaginationBtn, MonitorAction, MonitorCBD, HistoryCBD, HistoryAction
from api_telegram.statments import TargetFSM
from database import orm, ItemSearch
from database.exceptions import CustomError
from utils import target_price_validator

from utils.media import get_fs_input_hero_image, get_input_media_hero_image
import matplotlib.pyplot as plt

monitor = Router()


@monitor.message(Command("monitor"))
@monitor.callback_query(MonitorCBD.filter(F.action == MonitorAction.paginate))
@monitor.callback_query(MonitorCBD.filter(F.action == MonitorAction.list))
@monitor.callback_query(MonitorCBD.filter(F.action == MonitorAction.back))
async def list_monitoring(callback: types.CallbackQuery, callback_data: MonitorCBD = None):
    try:
        searched_items = await orm.monitoring.get_list(callback.from_user.id)
        if not searched_items:
            await callback.message.answer("Поисковые запросы отсутствуют.")
            return
        if callback_data is None:
            callback_data = HistoryCBD(
                action=HistoryAction.first,
                navigate=Navigation.first
            )
        manager = MonitorListManager(callback_data, callback.from_user.id)
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

    except CustomError as error:
        await callback.answer(
            text="⚠️ Ошибка\n{0:.150}".format(str(error)),
            show_alert=True
        )


@monitor.callback_query(MonitorCBD.filter(F.action == MonitorAction.add))
async def add_monitoring(callback: types.CallbackQuery, callback_data: MonitorCBD):
    try:
        manager = MonitorAddManager(callback_data, callback.from_user.id)
        await manager.start_monitoring_item()
        await callback.answer(
            text=f"✅ Товар добавлен в список мониторинга цен.",
            show_alert=True
        )
    except CustomError as error:
        await callback.answer(
            text="⚠️ Ошибка\n{0:.150}".format(str(error)),
            show_alert=True
        )


@monitor.callback_query(MonitorCBD.filter(F.action == MonitorAction.target))
async def add_target(callback: types.CallbackQuery, callback_data: MonitorCBD, state: FSMContext):
    kb_data = MonitorCBD(
        action=MonitorAction.list,
        navigate=callback_data.navigate,
        monitor_id=callback_data.monitor_id,
        item_id=callback_data.item_id,
        page=callback_data.page
    ).pack()

    await state.set_state(TargetFSM.product_id)
    await state.update_data(product_id=callback_data.item_id)
    await state.set_state(TargetFSM.callback)
    await state.update_data(callback=kb_data)
    await state.set_state(TargetFSM.price)

    kb = BasePaginationBtn()
    kb.add_button(kb.btn_data('back', kb_data)).add_markup(1)

    await callback.message.edit_media(
        media=await get_input_media_hero_image('target', msg="укажите желаемую цену"),
        reply_markup=kb.create_kb()
    )


@monitor.message(TargetFSM.price)
async def define_target_price(message: types.Message, state: FSMContext) -> None:
    try:
        defined_price = float(message.text)
        await target_price_validator(defined_price)
        await state.update_data(price=defined_price)
        state_data = await state.get_data()
        await state.clear()

        manager = DefineTargetManger(state_data)
        await manager.define_target()
        try:
            await message.bot.edit_message_media(
                chat_id=message.chat.id,
                message_id=int(message.message_id) - 1,
                media=await get_input_media_hero_image(
                    "success",
                    await manager.message()
                ),
                reply_markup=await manager.keyboard()
            )
            await message.bot.delete_message(
                chat_id=message.chat.id,
                message_id=message.message_id
            )
        except CustomError:
            await message.bot.send_photo(
                chat_id=message.chat.id,
                caption=await manager.message(),
                photo=await get_fs_input_hero_image('success'),
                reply_markup=await manager.keyboard()
            )
    except CustomError as error:
        await message.answer(
            text="⚠️ Ошибка\n{0:.150}".format(str(error)),
            show_alert=True
        )


@monitor.callback_query(MonitorCBD.filter(F.action == MonitorAction.delete))
async def delete_monitoring(callback: types.CallbackQuery, callback_data: MonitorCBD):
    try:
        manager = MonitorDeleteManager(callback_data, callback.from_user.id)
        await manager.stop_monitoring_item()
        await callback.answer(
            text="🗑 удален из списка мониторинга цен.",
            show_alert=True
        )
        await callback.message.edit_media(
            media=await manager.get_media(),
            reply_markup=await manager.get_keyboard()
        )
    except CustomError as error:
        await callback.answer(
            text="⚠️ Ошибка\n{0:.150}".format(str(error)),
            show_alert=True
        )


# TODO refactoring graph
@monitor.callback_query(MonitorCBD.filter(F.action == MonitorAction.graph))
async def send_chart_image(callback: types.CallbackQuery, callback_data: MonitorCBD):
    # Пример: Получаем ID поискового запроса из аргументов команды
    try:
        # get item search ##############################################################
        try:
            item_search = await orm.monitoring.get_item_by_id(callback_data.item_id)
            if item_search is None:
                raise ValueError
        except (ValueError, ItemSearch.DoesNotExist):
            await callback.answer(
                text="Неверный ID поискового запроса.",
                show_alert=True
            )
            return
        # get item search ##############################################################

        # get data search ##############################################################
        # Получаем данные, связанные с поисковым запросом
        entries = await orm.monitoring.get_monitor_data(item_search)
        if not entries:
            await callback.answer("Данные отсутствуют.")
            return
        # get data search ##############################################################

        # install local ######################################################################
        locale.setlocale(category=locale.LC_ALL, locale="Russian")
        # install local ######################################################################

        # graph maker ######################################################################
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

        plt.text(0.99, 0.99,
                 f'Максимум: {max(values)}',
                 horizontalalignment='right',
                 verticalalignment='top',
                 transform=plt.gca().transAxes,
                 fontsize=25, color='white', bbox=dict(facecolor='red', alpha=0.8))
        plt.text(0.99, 0.90,
                 f'Минимум: {min(values)}',
                 horizontalalignment='right',
                 verticalalignment='top',
                 transform=plt.gca().transAxes,
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
        # graph maker ######################################################################

        # message ######################################################################
        msg = f"\r\n📈 max цена = {max(values)}\t({max_time_value})\r\n" \
              f"📉 min цена = {min(values)}\t({min_time_value})\r\n" \
              f"📅 текущая цена = {values[-1]}\t({timestamps[-1]})\r\n"
        photo = InputMediaPhoto(media=FSInputFile("graph.png"), caption=msg)
        # message ######################################################################

        # keyboard ######################################################################
        kb = BasePaginationBtn()
        kb_data = MonitorCBD(
            action=MonitorAction.list,
            navigate=callback_data.navigate,
            monitor_id=callback_data.monitor_id,
            item_id=callback_data.item_id,
            page=callback_data.page
        ).pack()
        kb.add_button(kb.btn_data('back', kb_data)).add_markup(1)
        # keyboard ######################################################################

        await callback.message.edit_media(media=photo, reply_markup=kb.create_kb())
    except CustomError as error:
        await callback.answer(
            text=f"⚠️ Ошибка\n{str(error)}",
            show_alert=True
        )
