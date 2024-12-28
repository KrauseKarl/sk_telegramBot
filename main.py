import asyncio

from aiogram import Bot, Dispatcher, types

from commands import private
from config import settings
from handlers import router

bot = Bot(token=settings.bot_token.get_secret_value())
dp = Dispatcher()

dp.include_router(router)


async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await bot.set_my_commands(
        commands=private, scope=types.BotCommandScopeAllPrivateChats()
    )
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        print("✅ BOT START")
        asyncio.run(main())
    except KeyboardInterrupt:
        print("❌ BOT STOP")
