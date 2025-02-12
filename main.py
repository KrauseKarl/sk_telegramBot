import asyncio

from aiogram import Bot, Dispatcher, types
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from database.db import *
from database.models import *
from telegram_api.commands import private
from telegram_api.routers.bases import base
from telegram_api.routers.categories import category
from telegram_api.routers.details import detail
from telegram_api.routers.favorites import favorite
from telegram_api.routers.histories import history
from telegram_api.routers.searches import search

bot = Bot(
    token=conf.bot_token.get_secret_value(),
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher()

dp.include_router(base)
dp.include_router(search)
dp.include_router(detail)
dp.include_router(category)
dp.include_router(history)
dp.include_router(favorite)


async def main():
    create_tables()
    await bot.delete_webhook(
        drop_pending_updates=True
    )
    await bot.set_my_commands(
        commands=private,
        scope=types.BotCommandScopeAllPrivateChats()
    )
    await dp.start_polling(bot)
    drop_table()


if __name__ == "__main__":
    try:
        # logging.basicConfig(level=logging.INFO, stream=sys.stdout)
        print("✅ *** BOT START")
        asyncio.run(main())
    except KeyboardInterrupt:
        print("❌ BOT STOP")
