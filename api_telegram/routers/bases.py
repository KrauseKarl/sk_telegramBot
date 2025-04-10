from aiogram import F, Router, exceptions, filters, types as t
from aiogram.fsm.context import FSMContext

from api_redis import RedisHandler
from api_telegram import kbm
from core import config
from database import orm, exceptions as exp
from utils import media

base = Router()


# START ################################################################################################################
@base.message(filters.CommandStart())
async def start_command(message: t.Message) -> None:
    """

    :param message:
    :return:
    """
    try:
        welcoming = await orm.users.get_or_create(user=message.from_user)
        msg = '{0}, {1}!'.format(welcoming, message.from_user.first_name)
        photo = await media.get_fs_input_hero_image("welcome")
        await message.answer_photo(
            photo=photo,
            caption=msg,
            reply_markup=await kbm.menu()
        )
    except exp.CustomError as error:
        msg, photo = await media.get_error_answer_photo(error)
        await message.answer_photo(
            photo=photo,
            caption=msg,
            reply_markup=await kbm.menu()
        )


# HELP #################################################################################################################
@base.message(filters.Command("help"))
@base.callback_query(F.data.startswith("help"))
async def info(callback: t.Message | t.CallbackQuery) -> None:
    """

    :param callback:
    :return:
    """
    try:
        if isinstance(callback, t.CallbackQuery):
            photo = await media.get_input_media_hero_image("help", config.HELP)
            await callback.message.edit_media(
                media=photo,
                reply_markup=await kbm.back()
            )
        else:
            await callback.answer_photo(
                photo=await media.get_fs_input_hero_image("help"),
                caption=config.HELP,
                reply_markup=await kbm.back()
            )
    except exp.CustomError as error:
        await callback.answer(
            text=f"⚠️ Ошибка\n{str(error)}",
            show_alert=True)


# MENU #################################################################################################################
@base.message(filters.Command("menu"))
@base.callback_query(F.data.startswith("menu"))
async def menu(callback: t.Message | t.CallbackQuery, state: FSMContext) -> None:
    """

    :param state:
    :param callback:
    :return:
    """
    await state.clear()
    try:
        if isinstance(callback, t.CallbackQuery):
            photo = await media.get_input_media_hero_image("menu")
            await callback.message.edit_media(
                media=photo,
                reply_markup=await kbm.menu()
            )
        else:
            await callback.answer_photo(
                photo=await media.get_fs_input_hero_image("menu"),
                reply_markup=await kbm.menu()
            )
    except exceptions.TelegramBadRequest:
        await callback.message.answer_photo(
            photo=await media.get_fs_input_hero_image('menu'),
            reply_markup=await kbm.menu()
        )
    except exp.CustomError as error:
        await callback.answer(
            text=f"⚠️ Ошибка\n{str(error)}",
            show_alert=True
        )


# ONLY FOR DEVELOP #####################################################################################################
# TODO delete this routes on production
@base.message(filters.Command("redis"))
async def get_key_cache(message):
    keys = await RedisHandler().get_keys()
    if keys:
        print("keys count = {0} {1}".format(
            len(keys),
            '\n'.join([f"🔑 {k}" for k in sorted(keys)]))
        )


@base.message(filters.Command("del"))
async def del_key_cache(message):
    await RedisHandler().flush_keys()
    print('redis delete all keys')


########################################################################################################################


@base.message()
async def unidentified_massage(message: t.Message):
    msg = (
        "❓❓❓\n"
        "команда {0} мне не известна\n\n"
        "/help для списка всех команд".format(message.text)
    )
    await message.answer(text=msg)
