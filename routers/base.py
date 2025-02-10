from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.types import CallbackQuery, Message

from database.exceptions import CustomError
from database.orm import *
from utils import *
from keyboards import *

base = Router()


# START #############################################################################################################
@base.message(CommandStart())
async def start_command(message: Message) -> None:
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
    try:
        media = await get_input_media_hero_image("help", conf.HELP),
    except CustomError as error:
        media = await get_error_answer_media(error)
    await callback.message.edit_media(media=media, reply_markup=await menu_kb())


# MENU #############################################################################################################
@base.message(Command("menu"))
async def menu_message(message: Message | CallbackQuery) -> None:
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
    try:
        media = await get_input_media_hero_image("menu")
    except CustomError as error:
        media = await get_error_answer_media(error),
    await callback.message.edit_media(media=media, reply_markup=await menu_kb())


@base.callback_query(F.data.startswith("delete_"))
async def delete_call(callback: CallbackQuery) -> None:
    try:
        qnt = int(callback.data.split('_')[-1])
        print(f"{qnt= }")
        qnt = qnt if qnt <= 8 else 8
        print(f"{qnt= }")
        print(range(qnt))
        for q in range(1, qnt+1):
            print(callback.message.message_id-q)
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
