from aiogram import F, Router, exceptions, filters
from aiogram import types as t
from aiogram.fsm.context import FSMContext

from src.api_telegram import kbm
from src.core import config
from src.database import exceptions as exp
from src.database import orm
from src.logger import logger as log
from src.utils import media

base = Router()


# START #######################################################################
@base.message(filters.CommandStart())
async def start_command(message: t.Message) -> None:
    """
    Возвращает приветственное сообщение + клавиатуру.

    :param message: Message
    :return: None
    """
    try:
        welcoming = await orm.users.get_or_create(user=message.from_user)
        msg = "{0}, {1}!".format(welcoming, message.from_user.first_name)
        photo = await media.get_fs_input_hero_image("welcome")
        await message.answer_photo(
            photo=photo, caption=msg, reply_markup=await kbm.menu()
        )
    except exp.CustomError as error:
        msg, photo = await media.get_error_answer_photo(error)
        await message.answer_photo(
            photo=photo, caption=msg, reply_markup=await kbm.menu()
        )


# HELP ########################################################################
@base.message(filters.Command("help"))
@base.callback_query(F.data.startswith("help"))
async def help_info(callback: t.Message | t.CallbackQuery) -> None:
    """
    Возвращает справочную информацию по использованию бота.

    :param callback: Message | CallbackQuery
    :return: None
    """
    try:
        if isinstance(callback, t.CallbackQuery):
            photo = await media.get_input_media_hero_image("help", config.HELP)
            await callback.message.edit_media(
                media=photo, reply_markup=await kbm.video()
            )
        else:
            await callback.answer_photo(
                photo=await media.get_fs_input_hero_image("help"),
                caption=config.HELP,
                reply_markup=await kbm.video(),
            )
    except exp.CustomError as error:
        msg = "{0:.150}".format(str(error))
        log.error_log.error(msg)
        await callback.answer(text=f"⚠️ Ошибка\n{msg}", show_alert=True)


@base.callback_query(F.data.startswith("instruction"))
async def instruction_video(callback: t.CallbackQuery) -> None:
    """
    Загружает видео-инструкцию по использованию бота.

    :param callback:CallbackQuery
    :return: None
    """
    await callback.message.answer_animation(
        animation=await media.get_fs_input_hero_image("instruction"),
        caption="Видеоинструкция по использованию бота",
        reply_markup=await kbm.delete(),
    )


# MENU ########################################################################
@base.message(filters.Command("menu"))
@base.callback_query(F.data.startswith("menu"))
async def main_menu(callback: t.Message | t.CallbackQuery, state: FSMContext) -> None:
    """
    Возвращает главное меню.

    :param state: FSMContext
    :param callback: Message | CallbackQuery
    :return: None
    """
    await state.clear()
    try:
        if isinstance(callback, t.CallbackQuery):
            photo = await media.get_input_media_hero_image("menu")
            await callback.message.edit_media(
                media=photo, reply_markup=await kbm.menu()
            )
        else:
            await callback.answer_photo(
                photo=await media.get_fs_input_hero_image("menu"),
                reply_markup=await kbm.menu(),
            )
    except exceptions.TelegramBadRequest:
        await callback.message.answer_photo(
            photo=await media.get_fs_input_hero_image("menu"),
            reply_markup=await kbm.menu(),
        )
    except exp.CustomError as error:
        msg = "{0:.150}".format(str(error))
        log.error_log.error(msg)
        await callback.answer(text=f"⚠️ Ошибка\n{msg}", show_alert=True)


@base.callback_query(F.data == "delete")
async def delete_message(callback: t.CallbackQuery):
    """
    Удаляет два сообщения.

    Сообщения об ошибки и само сообщение с некорректными данными.
    :param callback:CallbackQuery
    :return: None
    """
    await callback.bot.delete_messages(
        chat_id=callback.message.chat.id,
        message_ids=[callback.message.message_id - 1, callback.message.message_id],
    )


@base.message()
async def unidentified_massage(message: t.Message) -> None:
    """
    Работает со всеми не распознанными сообщениями

    :param message: Message
    :return: None
    """
    msg = (
        "❓❓❓\n"
        "команда {0} мне не известна\n\n"
        "/help для списка всех команд".format(message.text)
    )
    await message.answer(text=msg)
