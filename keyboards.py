from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

sort_keyboard = InlineKeyboardMarkup(
    row_width=2,
    inline_keyboard=[
        [
            InlineKeyboardButton(text='по умолчанию',  callback_data='default'),
            InlineKeyboardButton(text='⬆️ по возрастанию',  callback_data='priceAsc'),
            InlineKeyboardButton(text='️️⬇️ по убыванию',  callback_data='priceDesc'),
            InlineKeyboardButton(text='💰 по продажам',  callback_data='salesDesc')
        ]
    ]
)
