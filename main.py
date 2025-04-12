import asyncio
import sys

from aiogram import Bot, Dispatcher, enums, types as t
from aiogram.client.default import DefaultBotProperties

from src.api_telegram import commands, crud, routers as r
from src.core import conf, config
from src.database import db, exceptions
from src.logger import logger as log


async def main():
    bot = Bot(
        token=conf.bot_token.get_secret_value(),
        default=DefaultBotProperties(
            parse_mode=enums.ParseMode.HTML,
            show_caption_above_media=False
        )
    )
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

    # print_tree(r'C:\Users\Kucheriavenko Dmitri\github\telegramBot\src')
