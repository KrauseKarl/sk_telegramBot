from aiogram import F, Router, filters
from aiogram import types as t
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.utils.chat_action import ChatActionSender

from src.api_telegram import (
    BasePaginationBtn,
    HistoryAction,
    HistoryCBD,
    MonitorAction,
    MonitorCBD,
    Navigation,
    crud,
)
from src.api_telegram.statments import TargetFSM
from src.core.bot import bot
from src.database import exceptions, orm
from src.logger import logger as log
from src.utils import media, target_price_validator

monitor = Router()


@monitor.message(filters.Command("monitor"))
@monitor.callback_query(MonitorCBD.filter(F.action == MonitorAction.paginate))
@monitor.callback_query(MonitorCBD.filter(F.action == MonitorAction.list))
@monitor.callback_query(MonitorCBD.filter(F.action == MonitorAction.back))
async def get_monitoring_list(
        callback: t.CallbackQuery, callback_data: MonitorCBD = None
):
    """

    :param callback:
    :param callback_data:
    :return:
    """
    try:
        searched_items = await orm.monitoring.get_list(callback.from_user.id)
        if not searched_items:
            await callback.message.answer("Поисковые запросы отсутствуют.")
            return
        if callback_data is None:
            callback_data = HistoryCBD(
                action=HistoryAction.first, navigate=Navigation.first
            )
        manager = crud.MonitorListManager(callback_data, callback.from_user.id)
        if isinstance(callback, t.Message):
            await callback.answer_photo(
                photo=await manager.get_photo(),
                caption=await manager.get_msg(),
                reply_markup=await manager.get_keyboard(),
            )
        else:
            await callback.message.edit_media(
                media=await manager.get_media(),
                reply_markup=await manager.get_keyboard(),
            )

    except exceptions.CustomError as error:
        log.error_log.error(str(error))
        await callback.answer(
            text="⚠️ Ошибка\n{0:.150}".format(str(error)), show_alert=True
        )


@monitor.callback_query(MonitorCBD.filter(F.action == MonitorAction.add))
async def add_monitoring(callback: t.CallbackQuery, callback_data: MonitorCBD):
    """

    :param callback:
    :param callback_data:
    :return:
    """
    try:
        manager = crud.MonitorAddManager(callback_data, callback.from_user.id)
        await manager.start_monitoring_item()
        await callback.answer(
            text="✅ Товар добавлен в список мониторинга цен.",
            show_alert=True,
        )
    except exceptions.CustomError as error:
        log.error_log.error(str(error))
        await callback.answer(
            text="⚠️ Ошибка\n{0:.150}".format(str(error)), show_alert=True
        )


@monitor.callback_query(MonitorCBD.filter(F.action == MonitorAction.target))
async def add_target(
        callback: t.CallbackQuery, callback_data: MonitorCBD, state: FSMContext
):
    """

    :param callback:
    :param callback_data:
    :param state:
    :return:
    """
    try:
        kb_data = MonitorCBD(
            action=MonitorAction.list,
            navigate=callback_data.navigate,
            monitor_id=callback_data.monitor_id,
            item_id=callback_data.item_id,
            page=callback_data.page,
        ).pack()

        await state.set_state(TargetFSM.product_id)
        await state.update_data(product_id=callback_data.item_id)
        await state.set_state(TargetFSM.callback)
        await state.update_data(callback=kb_data)
        await state.set_state(TargetFSM.price)

        kb = BasePaginationBtn()
        kb.add_button(kb.btn_data("back", kb_data)).add_markup(1)

        await callback.message.edit_media(
            media=await media.get_input_media_hero_image(
                value="target", msg="укажите желаемую цену"
            ),
            reply_markup=kb.create_kb(),
        )
    except exceptions.CustomError as error:
        log.error_log.error(str(error))
        await callback.answer(
            text="⚠️ Ошибка\n{0:.150}".format(str(error)), show_alert=True
        )


@monitor.message(TargetFSM.price)
async def define_target_price(message: t.Message, state: FSMContext) -> None:
    """

    :param message:
    :param state:
    :return:
    """
    try:
        defined_price = float(message.text)
        await target_price_validator(defined_price)
        await state.update_data(price=defined_price)
        state_data = await state.get_data()
        await state.clear()

        manager = crud.DefineTargetManger(state_data)
        await manager.define_target()
        try:
            await message.bot.edit_message_media(
                chat_id=message.chat.id,
                message_id=int(message.message_id) - 1,
                media=await media.get_input_media_hero_image(
                    "success", await manager.message()
                ),
                reply_markup=await manager.keyboard(),
            )
            await message.bot.delete_message(
                chat_id=message.chat.id, message_id=message.message_id
            )
        except (exceptions.CustomError, TelegramBadRequest) as error:
            log.error_log.error(str(error))
            await message.bot.send_photo(
                chat_id=message.chat.id,
                caption=await manager.message(),
                photo=await media.get_fs_input_hero_image("success"),
                reply_markup=await manager.keyboard(),
            )
    except exceptions.CustomError as error:
        log.error_log.error(str(error))
        await message.answer(
            text="⚠️ Ошибка\n{0:.150}".format(str(error)), show_alert=True
        )


@monitor.callback_query(MonitorCBD.filter(F.action == MonitorAction.delete))
async def delete_monitoring(callback: t.CallbackQuery, callback_data: MonitorCBD):
    """

    :param callback:
    :param callback_data:
    :return:
    """
    try:
        manager = crud.MonitorDeleteManager(callback_data, callback.from_user.id)
        await manager.stop_monitoring_item()
        await callback.answer(
            text="🗑 удален из списка мониторинга цен.", show_alert=True
        )
        await callback.message.edit_media(
            media=await manager.get_media(),
            reply_markup=await manager.get_keyboard(),
        )
    except exceptions.CustomError as error:
        log.error_log.error(str(error))
        await callback.answer(
            text="⚠️ Ошибка\n{0:.150}".format(str(error)), show_alert=True
        )


# TODO refactoring graph
@monitor.callback_query(MonitorCBD.filter(F.action == MonitorAction.graph))
async def send_chart_image(callback: t.CallbackQuery, callback_data: MonitorCBD):
    """

    :param callback:
    :param callback_data:
    :return:
    """
    try:
        chat_id = callback.message.chat.id
        async with ChatActionSender.upload_photo(bot=bot, chat_id=chat_id, interval=1.0):
            graph_manager = crud.GraphManager(callback_data, callback.from_user.id)
            photo = await graph_manager.get_media()
            keyboard = await graph_manager.get_keyboard()
            await callback.message.edit_media(media=photo, reply_markup=keyboard)

    except (ValueError, exceptions.CustomError) as error:
        log.error_log.error(str(error))
        await callback.answer(text=f"⚠️ Ошибка\n{str(error)}", show_alert=True)
