from aiogram import F, Router, types as t
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext

from api_redis.handlers import RedisHandler
from api_telegram.keyboard.paginators import *
from api_telegram.keyboard.builders import kbm
from database import orm
from database.exceptions import CustomError
from utils.media import *

route = Router()


# START ################################################################################################################
@route.message(CommandStart())
async def start_command(message: t.Message) -> None:
    """

    :param message:
    :return:
    """
    try:
        welcoming = await orm.users.get_or_create(user=message.from_user)
        msg = '{0}, {1}!'.format(welcoming, message.from_user.first_name)
        photo = await get_fs_input_hero_image("welcome")
        await message.answer_photo(
            photo=photo,
            caption=msg,
            reply_markup=await kbm.menu()
        )
    except CustomError as error:
        msg, photo = await get_error_answer_photo(error)
        await message.answer_photo(
            photo=photo,
            caption=msg,
            reply_markup=await kbm.menu()
        )


# HELP #################################################################################################################
@route.message(Command("help"))
@route.callback_query(F.data.startswith("help"))
async def info(callback: t.Message | t.CallbackQuery) -> None:
    """

    :param callback:
    :return:
    """
    try:
        if isinstance(callback, t.CallbackQuery):
            media = await get_input_media_hero_image("help", config.HELP)
            await callback.message.edit_media(
                media=media,
                reply_markup=await kbm.back()
            )
        else:
            await callback.answer_photo(
                photo=await get_fs_input_hero_image("help"),
                caption=config.HELP,
                reply_markup=await kbm.back()
            )
    except CustomError as error:
        await callback.answer(
            text=f"⚠️ Ошибка\n{str(error)}",
            show_alert=True)


# MENU #################################################################################################################
@route.message(Command("menu"))
@route.callback_query(F.data.startswith("menu"))
async def menu(callback: t.Message | t.CallbackQuery, state: FSMContext) -> None:
    """

    :param state:
    :param callback:
    :return:
    """
    await state.clear()
    try:
        if isinstance(callback, t.CallbackQuery):
            media = await get_input_media_hero_image("menu")
            await callback.message.edit_media(
                media=media,
                reply_markup=await kbm.menu()
            )
        else:
            await callback.answer_photo(
                photo=await get_fs_input_hero_image("menu"),
                reply_markup=await kbm.menu()
            )
    except TelegramBadRequest:
        await callback.message.answer_photo(
            photo=await get_fs_input_hero_image('menu'),
            reply_markup=await kbm.menu()
        )
    except CustomError as error:
        await callback.answer(
            text=f"⚠️ Ошибка\n{str(error)}",
            show_alert=True
        )


# ONLY FOR DEVELOP #####################################################################################################
# TODO delete this routes on production
@route.message(Command("redis"))
async def get_key_cache(message):
    keys = await RedisHandler().get_keys()
    if keys:
        print("keys count = {0} {1}".format(
            len(keys),
            '\n'.join([f"🔑 {k}" for k in sorted(keys)]))
        )


@route.message(Command("del"))
async def del_key_cache(message):
    await RedisHandler().flush_keys()
    print('redis delete all keys')
