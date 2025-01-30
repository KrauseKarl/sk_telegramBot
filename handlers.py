from aiogram import F, Router, types
from aiogram.exceptions import AiogramError
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, InputFile, FSInputFile, InputMediaPhoto
from peewee import IntegrityError
from pydantic import ValidationError

from keyboards import *
from pagination import Paginator
from statments import *
from utils import *
from database.db import *
from config import *

router = Router()


@router.message(CommandStart())
async def start_command(message: types.Message) -> None:
    user, created = UserModel.get_or_create(
        user_id=message.from_user.id,
        user_name=message.from_user.username,
        first_name=message.from_user.first_name,
        last_name=message.from_user.last_name
    )
    History.create(user=message.from_user.id, command='start').save()
    if created:
        await message.answer('🟨 🤚 Добро пожаловать, {0}!'.format(
            message.from_user.first_name,
        ))
        return
    await message.answer('🟩 🤝 Рады снова видеть вас, {0}!'.format(
        message.from_user.first_name,
    ), reply_markup=main_keyboard)


# MENU #############################################################################################################
@router.message(Command("menu"))
async def menu(message: Message) -> None:
    try:
        photo = FSInputFile("C:\\Users\\Kucheriavenko Dmitri\\github\\telegramBot\\static\\menu.png")
        await message.answer_photo(photo=photo, reply_markup=main_keyboard)
    # await message.answer(text='Главное меню', reply_markup=main_keyboard)
    except Exception as err:
        print(err)

        await message.answer('⚠️ Что-то пошло не так с командой /menu')
        await message.answer(str(err))


@router.callback_query(F.data.startswith("menu"))
async def menu_call(callback: CallbackQuery) -> None:
    try:
        media = FSInputFile("C:\\Users\\Kucheriavenko Dmitri\\github\\telegramBot\\static\\menu.png")
        photo = InputMediaPhoto(media=media)
        await callback.message.edit_media(media=photo, reply_markup=main_keyboard)
    except Exception as err:
        await callback.message.answer('⚠️ Что-то пошло не так с командой /menu')
        await callback.message.answer(str(err))


# HISTORY #############################################################################################################
# @router.callback_query(F.data.startswith("history"))
# async def history(call: CallbackQuery) -> None:
#     photo = FSInputFile("C:\\Users\\Kucheriavenko Dmitri\\github\\telegramBot\\static\\history.png")
#     await call.message.answer_photo(photo=photo)
#     history_list = History.select().where(
#         History.user == call.from_user.id
#     ).order_by(History.date)
#     for i in history_list:
#         msg = await history_info(i)
#         await call.message.answer(msg)
@router.callback_query(F.data.startswith("history"))
async def history_(callback: Message | CallbackQuery) -> None:
    print(callback.data)
    photo = FSInputFile("C:\\Users\\Kucheriavenko Dmitri\\github\\telegramBot\\static\\history.png")
    # await callback.message.answer_photo(photo=photo)
    history_list = History.select().where(
        History.user == callback.from_user.id
    ).order_by(History.date)
    keyboard = InlineKeyboardBuilder()
    if F.data.startswith("history"):
        page = 1
        call_back_data = "page_next_{0}".format(int(page) + 1)
        print(call_back_data)
        keyboard.add(InlineKeyboardButton(text='След. ▶', callback_data=call_back_data))
        keyboard.add(InlineKeyboardButton(text='главное меню', callback_data="menu"))
        paginator = Paginator(history_list, page=int(page))
        print(f"{paginator = }")
        history_item = paginator.get_page()[0]
        msg = await history_info(history_item)
        print(f"{msg = }")
        msg = msg + "{0} из {1}".format(page, paginator.pages)
        photo = InputMediaPhoto(media=photo, caption=msg)
        await callback.message.edit_media(media=photo, reply_markup=keyboard.adjust(1, 1).as_markup())


@router.callback_query(F.data.startswith("page"))
async def history_page(callback: Message | CallbackQuery) -> None:
    history_list = History.select().where(History.user == callback.from_user.id).order_by(History.date)
    keyboard = InlineKeyboardBuilder()
    if F.data.startswith("page"):
        page = int(callback.data.split("_")[2])
        paginator = Paginator(history_list, page=int(page))
        print(f"{paginator = }")
        history_item = paginator.get_page()[0]
        msg = await history_info(history_item)
        msg = msg + "{0} из {1}".format(page, paginator.pages)

        if callback.data.startswith("page_next"):
            callback_previous = "page_previous_{0}".format(page - 1)
            keyboard.add(InlineKeyboardButton(text="◀ Пред.", callback_data=callback_previous))
            if page != paginator.pages:
                callback_next = "page_next_{0}".format(page + 1)
                keyboard.add(InlineKeyboardButton(text='След. ▶', callback_data=callback_next))
        elif callback.data.startswith("page_previous"):
            if page != 1:
                callback_previous = "page_previous_{0}".format(page - 1)
                keyboard.add(InlineKeyboardButton(text="◀ Пред.", callback_data=callback_previous))
            callback_next = "page_next_{0}".format(page + 1)
            keyboard.add(InlineKeyboardButton(text='След. ▶', callback_data=callback_next))
        keyboard.add(InlineKeyboardButton(text='главное меню', callback_data="menu"))
        try:
            photo = types.InputMediaPhoto(media=history_item.image, caption=msg)
        except ValidationError:
            media = FSInputFile("C:\\Users\\Kucheriavenko Dmitri\\github\\telegramBot\\static\\history.png")
            photo = InputMediaPhoto(media=media, caption=msg)
            #
        await callback.message.edit_media(media=photo, reply_markup=keyboard.adjust(2, 1).as_markup())


# ITEM LIST ############################################################################################################
@router.callback_query(F.data.startswith("search"))
async def search_name(call: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(Form.product)
    await call.message.answer("🛍️ Введите название товара.")


@router.message(Form.product)
async def search_sort(message: Message, state: FSMContext) -> None:
    await state.update_data(product=message.text)
    await state.set_state(Form.sort)
    photo = FSInputFile("C:\\Users\\Kucheriavenko Dmitri\\github\\telegramBot\\static\\sort.png")
    await message.answer_photo(photo=photo, caption="Как отсортировать результат?", reply_markup=sort_keyboard)
    # await message.answer("Как отсортировать результат?", reply_markup=sort_keyboard)


@router.callback_query(Form.sort, F.data.in_(SORT_SET))
async def search_qnt(call: CallbackQuery, state: FSMContext) -> None:
    await state.update_data(sort=call.data)
    await state.set_state(Form.qnt)
    img = FSInputFile("C:\\Users\\Kucheriavenko Dmitri\\github\\telegramBot\\static\\quantity.png")
    photo = InputMediaPhoto(media=img, caption="сколько единиц товара вывести?")
    await call.message.edit_media(media=photo, reply_markup=await get_qnt_kb())


@router.callback_query(Form.qnt, F.data.in_(BTNS))
async def search_result(call: CallbackQuery, state: FSMContext) -> None:
    await state.update_data(qnt=call.data)
    data = await state.get_data()
    try:
        query = data["product"]
        sort = data["sort"]
        ranges = int(data["qnt"])
        await call.answer(f"⌛ searching {query}")
        # for _ in range(ranges):
        #     await call.message.answer('🛍️ {0} товар'.format(_))
        result = await request_handler(
            q=query,
            sort=sort,
            current_url="item_search_2"
        )

        try:
            print(result["message"])
            print("❌ лимит бесплатных API превышен")
        except KeyError:
            pass

        item_list = result["result"]["resultList"][:ranges]
        currency = result["result"]["settings"]["currency"]
        price_range__list = []
        for i in item_list:
            msg = card_info(i, currency)
            item_id_kb = await item_kb(i["item"]["itemId"])
            price = i["item"]["sku"]["def"]["promotionPrice"]
            price_range__list.append(price)
            await call.message.answer(msg, reply_markup=item_id_kb)
        price_range = get_price_range(price_range__list)

        History().create(
            user=call.from_user.id,
            command='search',
            search_name=query,
            result_qnt=int(ranges),
            price_range=price_range
        ).save()
        await state.clear()
    except AiogramError as err:
        await call.message.answer("⚠️ Ошибка\n{0}".format(str(err)))


# ITEM DETAIL ##########################################################################################################
@router.callback_query(F.data.startswith("item"))
async def get_item_detail(call: CallbackQuery, state: FSMContext) -> None:
    print("+", call.data)
    item_id = str(call.data).split("_")[1]
    response = await request_detail_2(item_id)
    title = response["result"]["item"]["title"]
    price = response["result"]["item"]["sku"]["base"][0]["promotionPrice"]
    reviews = response["result"]["reviews"]["count"]
    star = response["result"]["reviews"]["averageStar"]
    item_url = ":".join(["https", response["result"]["item"]["itemUrl"]])
    try:
        img = response["result"]["item"]["sku"]["props"][1]["values"][0]
        print(img)
        hero_img = ":".join(["https", img["image"]])
    except:
        hero_img = None
    History().create(
        user=call.from_user.id,
        command='item',
        title=title,
        price=price,
        reviews=reviews,
        stars=star,
        url=item_url,
        image=hero_img
    ).save()
    try:
        msg = detail_info_2(response)
        await call.message.answer(msg)

        img_color = detail_color_img(response)
        if img_color is not None:
            image_color_list = list(separate_img_by_ten(img_color, 9))
            await call.message.answer(
                "Количество цветов {0}".format(len(img_color))
            )
            for img in image_color_list:
                color_images = [types.InputMediaPhoto(media=i) for i in img]
                await call.message.answer_media_group(color_images)
        images = detail_img(response)
        if images is not None:
            image_color_list = list(separate_img_by_ten(images, 9))
            await call.message.answer("Все иллюстрации")
            for img in image_color_list:
                color_images = [types.InputMediaPhoto(media=i) for i in img]
                await call.message.answer_media_group(color_images)

    except AiogramError as err:
        err = response["result"]["status"]["data"]
        msg = response["result"]["status"]["msg"]["data-error"]
        await call.message.answer(f"⚠️ Произошла ошибка{err}.")
        await call.message.answer(msg)


# CATEGORY  ###########################################################################################################
@router.callback_query(F.data.startswith("category"))
async def search_category(call: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(CategoryForm.name)
    await call.message.answer("🛍️ Введите название товара или категории.")
    print("⌛ searching...")


@router.message(CategoryForm.name)
async def search_category_sort(message: Message, state: FSMContext) -> None:
    q = message.text
    await state.update_data(name=q)
    await message.answer("⌛ searching.")
    result = await request_handler(current_url="category_list_1")
    item_list = result["result"]["resultList"]
    await state.clear()
    for i in item_list:
        msg = category_info(i, q)
        if msg is not None:
            await message.answer(**msg.as_kwargs())
