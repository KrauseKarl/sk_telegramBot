from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

sort_keyboard = InlineKeyboardMarkup(
    row_width=2,
    inline_keyboard=[
        [
            InlineKeyboardButton(text="по умолчанию", callback_data="default"),
            InlineKeyboardButton(
                text="⬆️ по возрастанию", callback_data="priceAsc"
            ),
            InlineKeyboardButton(
                text="️️⬇️ по убыванию", callback_data="priceDesc"
            ),
            InlineKeyboardButton(
                text="💰 по продажам", callback_data="salesDesc"
            ),
        ]
    ],
)


async def item_kb(item_id: str):
    call = "item_{0}".format(item_id)
    item_keyboard = InlineKeyboardMarkup(
        row_width=1,
        inline_keyboard=[
            [
                InlineKeyboardButton(text="подробно", callback_data=call),
            ]
        ],
    )
    return item_keyboard
