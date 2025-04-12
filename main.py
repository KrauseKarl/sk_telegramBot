from pathlib import Path

from aiogram import Bot, Dispatcher, enums, types as t
from aiogram.client.default import DefaultBotProperties

from src.api_telegram import commands, crud, routers as r
from src.core import conf
from src.database import db


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


# # todo delete after dev. Make folder-tree
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
#
# # todo delete after dev. Make folder-tree


if __name__ == "__main__":
    # try:
    #     log.set_logger_files()
    #     log.info_log.info(sys.platform)
    #     log.info_log.info(config.MODE_MASSAGE)
    #     asyncio.run(main())
    # except exceptions.TelegramBadRequest as error:
    #     log.error_log.error(str(error))
    # except KeyboardInterrupt:
    #     log.error_log.info("❌ BOT STOP")

    print_tree(r'C:\Users\Kucheriavenko Dmitri\github\telegramBot\src')
