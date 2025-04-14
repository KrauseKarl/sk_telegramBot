from aiogram import F, Router, exceptions, filters
from aiogram import types as t
from aiogram.fsm.context import FSMContext
from aiogram.utils.chat_action import ChatActionSender

from src.api_telegram import DetailAction, DetailCBD, ItemCBD, crud, kbm, statments
from src.core.bot import bot
from src.database import exceptions as expt
from src.logger import logger as log
from src.utils import media, validators

search = Router()


@search.message(filters.Command("search"))
async def search_name_message(message: t.Message, state: FSMContext) -> None:
    """
    Запрос названия товара для поиска.

    :param message: Message
    :param state: FSMContext
    :return: None
    """
    try:
        await state.clear()  # очистка машины-состояния
        await state.set_state(statments.ItemFSM.product)
        await message.answer_photo(
            photo=await media.get_fs_input_hero_image("search"),
            caption="🛍️ Введите название товара.",
        )
    except expt.CustomError as error:
        msg = "{0:.150}".format(str(error))
        log.error_log.error(msg)
        await message.answer(text=f"⚠️ Ошибка\n{msg}", show_alert=True)


@search.callback_query(F.data.startswith("search"))
async def search_name_callback(callback: t.CallbackQuery, state: FSMContext) -> None:
    """
    Запрос названия товара для поиска.

    :param callback: CallbackQuery
    :param state: FSMContext
    :return: None
    """
    try:
        await state.clear()  # очистка машины-состояния
        await state.set_state(statments.ItemFSM.product)
        try:
            await callback.message.edit_media(
                media=await media.get_input_media_hero_image(
                    "search",
                    "🛍️ {0}, Введите название товара.".format(
                        callback.from_user.username
                    ),
                )
            )
        except exceptions.TelegramBadRequest:
            await callback.message.answer_photo(
                photo=await media.get_fs_input_hero_image("search"),
                caption="🛍️ Введите название товара.",
            )
    except expt.CustomError as error:
        msg = "{0:.150}".format(str(error))
        log.error_log.error(msg)
        await callback.answer(text=f"⚠️ Ошибка\n{msg}", show_alert=True)


@search.message(statments.ItemFSM.product)
async def search_price_range(message: t.Message, state: FSMContext) -> None:
    """
    Запрос на ценовой диапазон.

    Если пользователь нажимает `да`,
    то переходит к запросу min и max цены.
    Есл же пользователь выбирает `пропустить` -
    переходит к запросу сортировки поискового запроса.
    :param message:
    :param state:
    :return:
    """
    try:
        # await RedisHandler().flush_keys()  # очистка всего кэша в Redis
        await state.update_data(product=message.text)
        await message.bot.edit_message_media(
            chat_id=message.chat.id,
            message_id=int(message.message_id) - 1,
            media=await media.get_input_media_hero_image(
                "range", "Задать ценовой диапазон?"
            ),
            reply_markup=await kbm.price_range(),
        )
        await message.bot.delete_message(
            chat_id=message.chat.id, message_id=message.message_id
        )
    except exceptions.TelegramBadRequest:
        await message.answer_photo(
            photo=await media.get_fs_input_hero_image("range"),
            caption="Задать ценовой диапазон?",
            reply_markup=await kbm.price_range(),
        )
    except expt.CustomError as error:
        msg = "{0:.150}".format(str(error))
        log.error_log.error(msg)
        await message.answer(text=f"⚠️ Ошибка\n{msg}", show_alert=True)


@search.callback_query(F.data.startswith("price_min"))
async def search_price_min(callback: t.CallbackQuery, state: FSMContext) -> None:
    """
    Запрос на минимальную цену поиска товара.

    :param callback: CallbackQuery
    :param state: FSMContext
    :return: None
    """
    try:
        await state.set_state(statments.ItemFSM.price_min)

        await callback.message.edit_media(
            media=await media.get_input_media_hero_image(
                "price_min", "Укажите минимальную  цену?"
            )
        )
    except expt.CustomError as error:
        msg = "{0:.150}".format(str(error))
        log.error_log.error(msg)
        await callback.answer(text=f"⚠️ Ошибка\n{msg}", show_alert=True)


@search.message(statments.ItemFSM.price_min)
async def search_price_max(message: t.Message, state: FSMContext) -> None:
    """
    Запрос на максимальную цену поиска товара.

    :param message: Message
    :param state: FSMContext
    :return: None
    """
    try:
        prev_message = int(message.message_id) - 2
        await message.bot.delete_message(
            chat_id=message.chat.id, message_id=message.message_id
        )
        min_price = int(message.text) if message.text else 0
        await validators.min_price_validator(min_price)
        await state.update_data(price_min=min_price)
        await state.set_state(statments.ItemFSM.price_max)
        try:
            await message.bot.edit_message_media(
                chat_id=message.chat.id,
                message_id=prev_message,
                media=await media.get_input_media_hero_image(
                    "price_max", "Укажите максимальную цену?"
                ),
            )
        except exceptions.TelegramBadRequest:
            await message.bot.send_photo(
                chat_id=message.chat.id,
                photo=await media.get_fs_input_hero_image("price_max"),
                caption="Укажите максимальную цену?",
            )
    except (expt.CustomError, ValueError) as error:
        msg = "{0:.150}".format(str(error))
        log.error_log.error(msg)
        await message.answer(text=f"⚠️ Ошибка\n{msg}", show_alert=True)


# SORT ########################################################################
@search.message(statments.ItemFSM.price_max)
async def search_sort_add_price_range(message: t.Message, state: FSMContext) -> None:
    """
    Запрос на сортировку поисковой выдачи.

    :param message: Message
    :param state: FSMContext
    :return: None
    """
    try:
        prev_message = int(message.message_id) - 3
        await message.bot.delete_message(
            chat_id=message.chat.id, message_id=message.message_id
        )
        min_price = int(await state.get_value("price_min"))
        max_price = int(message.text)
        await validators.min_price_validator(min_price)
        await validators.max_price_validator(min_price, max_price)
        await state.update_data(price_max=max_price)
        await state.set_state(statments.ItemFSM.sort)

        await message.bot.edit_message_media(
            chat_id=message.chat.id,
            message_id=prev_message,
            media=await media.get_input_media_hero_image(
                "sort", "Как отсортировать результат?"
            ),
            reply_markup=await kbm.sort(),
        )
    except (expt.CustomError, ValueError) as error:
        msg = "{0:.150}".format(str(error))
        log.error_log.error(msg)
        await message.answer(text=f"⚠️ Ошибка\n{msg}", show_alert=True)


@search.callback_query(F.data.startswith("price_skip"))
async def search_sort_skip_price_range(
    callback: t.CallbackQuery, state: FSMContext
) -> None:
    """
    Запрос на сортировку поисковой выдачи.

    Срабатывает, когда пользователь пропускает шаг по установки
    минимальной и максимальной цены. Без указания ценового диапазона.
    :param callback: CallbackQuery
    :param state: FSMContext
    :return: None
    """
    try:
        await state.set_state(statments.ItemFSM.sort)
        await callback.message.edit_media(
            media=await media.get_input_media_hero_image(
                "sort", "Как отсортировать результат?"
            ),
            reply_markup=await kbm.sort(),
        )
    except expt.CustomError as error:
        msg = "{0:.150}".format(str(error))
        log.error_log.error(msg)
        await callback.answer(text=f"⚠️ Ошибка\n{msg}", show_alert=True)


@search.callback_query(statments.ItemFSM.sort)
@search.callback_query(ItemCBD.filter())
@search.callback_query(DetailCBD.filter(F.action == DetailAction.back_list))
async def search_result(
    callback: t.CallbackQuery,
    state: FSMContext,
    callback_data: ItemCBD | DetailCBD | None = None,
) -> None:
    """
    Возвращает список поисковой выдачи.

    :param callback_data: ItemCBD | DetailCBD
    :param callback: CallbackQuery
    :param state: FSMContext
    :return: None
    """
    try:
        chat_id = callback.message.chat.id
        async with ChatActionSender.upload_photo(
            bot=bot, chat_id=chat_id, interval=1.0
        ):
            await callback.answer()
            manager = crud.ItemManager(
                state=state, callback=callback, callback_data=callback_data
            )
            try:
                await callback.message.edit_media(
                    media=await manager.get_media(),
                    reply_markup=await manager.keyboard(),
                )
            except exceptions.TelegramBadRequest:
                await callback.message.answer_photo(
                    photo=await manager.get_photo(),
                    caption=await manager.get_message(),
                    reply_markup=await manager.keyboard(),
                )
    except expt.CustomError as error:
        msg = "{0:.150}".format(str(error))
        log.error_log.error(msg)
        await callback.answer(text=f"⚠️ Ошибка\n{msg}", show_alert=True)
