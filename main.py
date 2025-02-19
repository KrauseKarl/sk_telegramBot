import asyncio

from aiogram import Bot, Dispatcher, types
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from database.db import *
from database.models import *
from telegram_api import routers, commands


bot = Bot(
    token=conf.bot_token.get_secret_value(),
    default=DefaultBotProperties(
        parse_mode=ParseMode.HTML,
        show_caption_above_media=False
    )
)
dp = Dispatcher()

dp.include_router(routers.bases.base)
dp.include_router(routers.searches.search)
dp.include_router(routers.details.detail)
dp.include_router(routers.categories.category)
dp.include_router(routers.histories.history)
dp.include_router(routers.favorites.favorite)


async def main():
    create_tables()
    await bot.delete_webhook(
        drop_pending_updates=True
    )
    await bot.set_my_commands(
        commands=commands.private,
        scope=types.BotCommandScopeAllPrivateChats()
    )
    await dp.start_polling(bot)

    drop_table()


if __name__ == "__main__":
    try:
        # logging.basicConfig(level=logging.INFO, stream=sys.stdout)
        print("🟥🟩🟦 BOT START 🟥🟩🟦")
        asyncio.run(main())
    except KeyboardInterrupt:
        print("❌ BOT STOP")
