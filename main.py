import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher, types
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from api_telegram import commands, routers as r
from api_telegram.crud.schedules import ScheduleManager
from core import config
from database.db import *
from database.models import *



async def main():
    bot = Bot(
        token=conf.bot_token.get_secret_value(),
        default=DefaultBotProperties(
            parse_mode=ParseMode.HTML,
            show_caption_above_media=False
        )
    )
    dp = Dispatcher()
    dp.include_routers(
        r.route,
        r.monitor,
        r.history,
        r.favorite,
        r.search,
        r.detail,
        r.review
    )
    create_tables()
    schedule_manager = ScheduleManager(bot)
    await schedule_manager.setup_scheduler()
    # await setup_scheduler(bot)

    await bot.delete_webhook(
        drop_pending_updates=True
    )
    await bot.set_my_commands(
        commands=commands.private,
        scope=types.BotCommandScopeAllPrivateChats()
    )
    await dp.start_polling(bot)

    drop_table()


# todo delete after dev. Make folder-tree
def print_tree(directory, prefix=''):
    paths = sorted(Path(directory).iterdir())
    for i, path in enumerate(paths):

        if path.name not in ['__pycache__', '__init__.py']:
            if i == len(paths) - 1:
                new_prefix = prefix + '    '
                print(prefix + '└── ' + path.name)
            else:

                new_prefix = prefix + '│   '
                print(prefix + '├── ' + path.name)
            if path.is_dir():
                print_tree(path, new_prefix)


# todo delete after dev. Make folder-tree

if __name__ == "__main__":
    try:
        logging.basicConfig(level=logging.INFO, stream=sys.stdout)
        msg = f"🟨☢️ BOT START FAKE_MODE = {config.FAKE_MODE}" if config.FAKE_MODE \
            else f"🟩🌐 BOT START FAKE_MODE = {config.FAKE_MODE}"
        logging.info(msg)
        print(msg)
        asyncio.run(main())
    except KeyboardInterrupt:
        print("❌ BOT STOP")
    # print_tree(r'C:\Users\Kucheriavenko Dmitri\github\telegramBot\api_telegram')
