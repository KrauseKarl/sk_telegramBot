import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher, types

from commands import private
from config import settings
from database.models import db, UserModel, ItemListModel, ItemDetailModel
from handlers import router
from database.db import create_tables, drop_table

bot = Bot(token=settings.bot_token.get_secret_value())
dp = Dispatcher()

dp.include_router(router)


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
        print("✅ BOT START")
        asyncio.run(main())
    except KeyboardInterrupt:
        print("❌ BOT STOP")
