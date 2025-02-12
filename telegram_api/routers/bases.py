from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.types import CallbackQuery, Message

from core import config
from database.exceptions import CustomError
from database.orm import *
from telegram_api.keyboards import *
from utils.media import *

base = Router()


# START #############################################################################################################
@base.message(CommandStart())
async def start_command(message: Message) -> None:
    """

    :param message:
    :return:
    """
    try:
        welcoming = await orm_get_or_create_user(user=message.from_user)
        msg = '{0}, {1}!'.format(welcoming, message.from_user.first_name)
        await message.answer(msg, reply_markup=await menu_kb())
    except CustomError as error:
        msg, photo = await get_error_answer_photo(error)
        await message.answer_photo(
            photo=photo,
            caption=msg,
            reply_markup=await menu_kb()
        )


# HELP #############################################################################################################
@base.message(Command("help"))
async def help_command(message: Message) -> None:
    """

    :param message:
    :return:
    """
    try:
        await message.answer_photo(
            photo=await get_fs_input_hero_image("help"),
            caption=conf.HELP,
            reply_markup=await menu_kb()
        )
    except CustomError as error:
        msg, photo = await get_error_answer_photo(error)
        await message.answer_photo(
            photo=photo,
            caption=msg,
            reply_markup=await menu_kb()
        )


@base.callback_query(F.data.startswith("help"))
async def help_call(callback: CallbackQuery) -> None:
    """

    :param callback:
    :return:
    """
    try:
        media = await get_input_media_hero_image("help", conf.HELP),
    except CustomError as error:
        media = await get_error_answer_media(error)
    await callback.message.edit_media(media=media, reply_markup=await menu_kb())


# MENU #############################################################################################################
@base.message(Command("menu"))
async def menu_message(message: Message | CallbackQuery) -> None:
    """

    :param message:
    :return:
    """
    try:
        await message.answer_photo(
            photo=await get_fs_input_hero_image("menu"),
            reply_markup=await menu_kb()
        )
    except Exception as error:
        msg, photo = await get_error_answer_photo(error)
        await message.answer_photo(
            photo=photo,
            caption=msg
        )


@base.callback_query(F.data.startswith("menu"))
async def menu_call(callback: CallbackQuery) -> None:
    """

    :param callback:
    :return:
    """
    try:
        media = await get_input_media_hero_image("menu")
        # await callback.message.edit_reply_markup(
        #     reply_markup=ReplyKeyboardMarkup(
        #         resize_keyboard=True,
        #         keyboard=[
        #             [
        #                 KeyboardButton(text='menu')
        #             ]
        #         ]
        #     )
        # )
    except CustomError as error:
        media = await get_error_answer_media(error),
    await callback.message.edit_media(media=media, reply_markup=await menu_kb())


@base.callback_query(F.data.startswith("delete_"))
async def delete_call(callback: CallbackQuery) -> None:
    """

    :param callback:
    :return:
    """
    try:
        qnt = int(callback.data.split('_')[-1])
        qnt = qnt if qnt <= config.IMG_LIMIT else config.IMG_LIMIT
        for q in range(1, qnt + 1):
            await callback.message.bot.delete_message(
                chat_id=callback.message.chat.id,
                message_id=callback.message.message_id-q
            )
        await callback.message.bot.delete_message(
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id
        )
    except CustomError as error:
        media = await get_error_answer_media(error)
        await callback.message.edit_media(
            media=media,
            reply_markup=await menu_kb()
        )
