from aiogram import Bot, enums
from aiogram.client.default import DefaultBotProperties

from src.core import conf

bot = Bot(
    token=conf.bot_token.get_secret_value(),
    default=DefaultBotProperties(
        parse_mode=enums.ParseMode.HTML,
        show_caption_above_media=False
    )
)
