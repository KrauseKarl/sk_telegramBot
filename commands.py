from aiogram.types import BotCommand

private = [
    BotCommand(command="menu", description="главное меню"),
    BotCommand(command="search", description="поиск товара"),
    BotCommand(command="category", description="поиск категории"),
    BotCommand(command="history", description="история запросов"),
]
