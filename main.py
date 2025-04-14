import asyncio
import sys

from aiogram import Dispatcher, exceptions, types as t

from src.api_telegram import commands, crud, routers as r
from src.core import config
from src.core.bot import bot
from src.database import db
from src.logger import logger as log


async def main():
    dp = Dispatcher()
    dp.include_routers(
        r.monitor,
        r.history,
        r.favorite,
        r.search,
        r.detail,
        r.review,
        r.base,
    )
    db.create_tables()
    schedule_manager = crud.ScheduleManager(bot)
    await schedule_manager.setup_scheduler()
    # await setup_scheduler(bot)

    await bot.delete_webhook(
        drop_pending_updates=True
    )
    await bot.set_my_commands(
        commands=commands.private,
        scope=t.BotCommandScopeAllPrivateChats()
    )
    await dp.start_polling(bot)

    db.drop_table()


if __name__ == "__main__":
    try:
        log.set_logger_files()
        log.info_log.info(sys.platform)
        log.info_log.info(config.MODE_MASSAGE)
        asyncio.run(main())
    except exceptions.TelegramBadRequest as error:
        log.error_log.error(str(error))
    except KeyboardInterrupt:
        log.error_log.info("❌ BOT STOP")

    # print_tree()
    # mypy src/
    # flake8 --max-line-length 88 src/
    # isort --line-length 88 --profile black src/
    # black   --line-length 88 src/

