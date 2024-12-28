import asyncio
import requests
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart, Command

from config import settings, SORT
from commands import private

bot = Bot(token=settings.bot_token.get_secret_value())
dp = Dispatcher()


# dp.include_router(router)
# dp.include_router(router_utils)


@dp.message(CommandStart())
async def start_command(message: types.Message):
    await message.answer('Привет! Я виртуальный помощник 😀')


@dp.message(Command("search"))
async def investing(message):
    print('⌛ searching...')
    await message.answer('⌛ searching.')
    # try:
    ranges = settings.range
    result = print_hi(
        q='Кроссовки',
        sort=SORT['default'],
        current_url='item_search_2'
    )
    item_list = result["result"]['resultList'][:ranges]
    currency = result["result"]['settings']['currency']
    for i in item_list:
        msg = card_info(i, currency)
        await message.answer(msg)
    # except Exception as err:
    #     bot.send_message(
    #         message.from_user.id,
    #         '❌Я тебя не понимаю, напиши "/help.'
    #     )


@dp.message(Command('category'))
async def investing(message):
    print('⌛ searching...')
    await message.answer('⌛ searching.')
    result = print_hi(current_url='category_list_1')
    item_list = result["result"]['resultList']
    for i in item_list:
        msg = category_info(i)
        await message.answer(msg)


def print_hi(current_url, q=None, sort=None) -> dict:
    headers = {
        "x-rapidapi-key": settings.api_key.get_secret_value(),
        "x-rapidapi-host": settings.host
    }
    base_url = settings.url
    url = base_url + '/' + current_url
    querystring = {"locale": "ru_RU", "currency": "RUB", "region": "RU", }
    if q and sort:
        querystring['q'] = q
        querystring["sort"] = sort
    response = requests.get(
        url=url,
        headers=headers,
        params=querystring
    )
    return response.json()


def card_info(i, currency):
    title = i["item"]["title"]
    sales = i["item"]["sales"]
    price = i["item"]["sku"]["def"]["promotionPrice"]
    image_url = ":".join(["https", i["item"]["itemUrl"]])
    image = ":".join(["https", i["item"]["image"]])
    msg = "название: {0}\n продано: {1}\n цена: {2} {3}\n{5}".format(
        title, sales, price, currency, image_url, image
    )
    # await message.answer(msg)
    return msg


def category_info(i):
    category_name = i["name"]
    msg = "{0}\n".format(category_name)
    sub_category_name = i["list"]
    for s in sub_category_name:
        sub_name = s['name']
        msg = msg + "- {0}\n".format(sub_name)
    # await message.answer(msg)
    return msg


async def main():
    await bot.delete_webhook(
        drop_pending_updates=True
    )
    await bot.set_my_commands(
        commands=private,
        scope=types.BotCommandScopeAllPrivateChats()
    )
    await dp.start_polling(bot)


if __name__ == '__main__':
    try:
        print("✅ BOT START")
        asyncio.run(main())
    except KeyboardInterrupt:
        print("❌ BOT STOP")
