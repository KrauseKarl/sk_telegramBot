import os.path

from aiogram import F, Router, types
from aiogram.exceptions import AiogramError
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, InputFile, FSInputFile, InputMediaPhoto
from peewee import IntegrityError
from pydantic import ValidationError
from aiogram.types.photo_size import PhotoSize
from keyboards import *
from pagination import Paginator
from statments import *
from utils import *
from database.db import *
from config import *
from request import request_item_detail, request_item_list

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
        static_folder = settings.static_path
        path = os.path.join(static_folder, 'menu.png')
        print(f"{path = }")
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
        photo = InputMediaPhoto(media=photo, caption=msg, parse_mode="HTML")
        await callback.message.edit_media(media=photo, reply_markup=keyboard.adjust(1, 1).as_markup())


@router.callback_query(F.data.startswith("page"))
async def history_page(callback: Message | CallbackQuery) -> None:
    history_list = History.select().where(History.user == callback.from_user.id).order_by(History.date)
    keyboard = InlineKeyboardBuilder()
    if F.data.startswith("page"):
        page = int(callback.data.split("_")[2])
        paginator = Paginator(history_list, page=int(page))
        # print(f"{paginator = }")
        history_item = paginator.get_page()[0]
        msg = await history_info(history_item)
        msg = msg + "{0} из {1}".format(page, paginator.pages)

        if callback.data.startswith("page_next"):
            callback_previous = "page_previous_{0}".format(page - 1)
            keyboard.add(InlineKeyboardButton(text="◀ Пред.", callback_data=callback_previous))
            if page != paginator.pages:

                callback_next = "page_next_{0}".format(page + 1)
                keyboard.add(InlineKeyboardButton(text='След. ▶', callback_data=callback_next))
                if paginator.pages > 10:
                    callback_next = "page_next_{0}".format(page + 10)
                    keyboard.add(InlineKeyboardButton(text='След. 10 ▶', callback_data=callback_next))
        elif callback.data.startswith("page_previous"):
            if page != 1:

                callback_previous = "page_previous_{0}".format(page - 1)
                keyboard.add(InlineKeyboardButton(text="◀ Пред.", callback_data=callback_previous))
                if page > 10:
                    callback_previous = "page_previous_{0}".format(page - 10)
                    keyboard.add(InlineKeyboardButton(text="◀ Пред. 10", callback_data=callback_previous))

            callback_next = "page_next_{0}".format(page + 1)
            keyboard.add(InlineKeyboardButton(text='След. ▶', callback_data=callback_next))
        keyboard.add(InlineKeyboardButton(text='главное меню', callback_data="menu"))
        try:
            photo = types.InputMediaPhoto(media=history_item.image, caption=msg, show_caption_above_media=False)
        except ValidationError:
            media = FSInputFile("C:\\Users\\Kucheriavenko Dmitri\\github\\telegramBot\\static\\history.png")
            photo = InputMediaPhoto(media=media, caption=msg, parse_mode='HTML')

            #
        await callback.message.edit_media(
            media=photo,
            reply_markup=keyboard.adjust(2, 2, 1).as_markup())


# ITEM LIST ############################################################################################################
@router.callback_query(F.data.startswith("search"))
async def search_name(call: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(Form.product)
    path = os.path.join(settings.static_path, "cart.png")
    photo = InputMediaPhoto(media=FSInputFile(path), caption="🛍️ Введите название товара.")
    await call.message.edit_media(media=photo)


@router.message(Form.product)
async def search_sort(message: Message, state: FSMContext) -> None:
    await state.update_data(product=message.text)
    await state.set_state(Form.sort)
    path = os.path.join(settings.static_path, "sort.png")
    await message.answer_photo(
        photo=FSInputFile(path),
        caption="Как отсортировать результат?",
        reply_markup=sort_keyboard
    )


@router.callback_query(Form.sort, F.data.in_(SORT_SET))
async def search_qnt(call: CallbackQuery, state: FSMContext) -> None:
    await state.update_data(sort=call.data)
    await state.set_state(Form.qnt)
    path = os.path.join(settings.static_path, "quantity.png")
    photo = InputMediaPhoto(media=FSInputFile(path), caption="сколько единиц товара вывести?")
    await call.message.edit_media(media=photo, reply_markup=await get_qnt_kb())


@router.callback_query(Form.qnt, F.data.in_(BTNS))
async def search_result(call: CallbackQuery, state: FSMContext) -> None:
    await state.update_data(qnt=call.data)
    data = await state.get_data()
    search_data = dict()
    price_range_list = []
    try:
        await call.answer("⌛ searching {0}".format(data['product']))
        # for _ in range(ranges):
        #     await call.message.answer('🛍️ {0} товар'.format(_))
        result = await request_item_list(
            q=data["product"],
            sort=data["sort"],
            url="item_search_2"
        )
        try:
            print("{0}\n❌ лимит бесплатных API превышен".format(result["message"]))
        except KeyError:
            pass
        ranges = int(data["qnt"])
        item_list = result["result"]["resultList"][:ranges]
        currency = result["result"]["settings"]["currency"]

        for item in item_list:
            msg, img = card_info(item, currency)
            kb = await item_kb(item["item"]["itemId"])
            price = item["item"]["sku"]["def"]["promotionPrice"]
            price_range_list.append(price)
            await call.message.answer_photo(photo=img, caption=msg, reply_markup=kb, parse_mode="HTML")

        search_data['user'] = call.from_user.id
        search_data['command'] = 'search'
        search_data["price_range"] = get_price_range(price_range_list)
        search_data['result_qnt'] = int(ranges)
        search_data['search_name'] = data['product']
        History().create(**search_data).save()  # todo make orm func for orm.py

        await state.clear()
    except AiogramError as err:
        await call.message.answer("⚠️ Ошибка\n{0}".format(str(err)))


# ITEM DETAIL ##########################################################################################################
@router.callback_query(F.data.startswith("item"))
async def get_item_detail(call: CallbackQuery, state: FSMContext) -> None:
    item_data_dict = dict()
    item_id = str(call.data).split("_")[1]
    response = await request_item_detail(item_id)
    item = response["result"]["item"]
    reviews = response["result"]["reviews"]
    item_data_dict["user"] = call.from_user.id
    item_data_dict["command"] = "item detail"
    item_data_dict["title"] = item.get("title")
    item_data_dict["price"] = item.get("sku").get("base")[0].get("promotionPrice")
    item_data_dict["reviews"] = reviews.get("count")
    item_data_dict["star"] = reviews.get("averageStar")
    item_data_dict["url"] = ":".join(["https", item.get("itemUrl")])
    # try:
    print('\n#0 {0}'.format(item["images"]))
    img = item["images"][0]
    print(f'\n#1 {img= }')
    image_full_path = ":".join(["https", img])
    print(f'\n#2 {image_full_path= }')
    item_data_dict["image"] = image_full_path
    # except:
    #     static_folder = settings.static_path
    #     path = os.path.join(static_folder, 'category.png')
    #     image_full_path = FSInputFile(path)
    #     item_data_dict["image"] = None

    History().create(**item_data_dict).save()  # todo make orm func for orm.py

    # try:
    msg = detail_info_2(response)
    print('@@@', len(msg))
    if len(msg) > 1000:
        msg = msg[:999]
        print('@@@', len(msg))
    # photo = InputMediaPhoto(media=img, caption=msg)
    await call.message.answer_photo(photo=image_full_path, caption=msg)

    img_color = detail_color_img(response)
    if img_color is not None:
        image_color_list = list(separate_img_by_ten(img_color, 9))
        await call.message.answer("Количество цветов {0}".format(len(img_color)))
        for img in image_color_list:
            color_images = [types.InputMediaPhoto(media=i) for i in img]
            await call.message.answer_media_group(color_images)
    images = detail_img(response)
    if images is not None:
        image_color_list = list(separate_img_by_ten(images, 5))
        await call.message.answer("Все иллюстрации")
        for img in image_color_list:
            color_images = [types.InputMediaPhoto(media=i) for i in img]
            await call.message.answer_media_group(color_images, reply_markup=main_keyboard)
    await call.message.answer('_', reply_markup=main_keyboard)
    # except AiogramError as err:
    #     err = response["result"]["status"]["data"]
    #     # msg = response["result"]["status"]["msg"]["data-error"]
    #     await call.message.answer(f"⚠️ Произошла ошибка{err}.")
    #     await call.message.answer(msg)


# CATEGORY  ###########################################################################################################
@router.callback_query(F.data.startswith("category"))
async def search_category(call: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(CategoryForm.name)
    await call.message.answer("🛍️ Введите название товара или категории.")
    print("⌛ searching...")


@router.message(CategoryForm.name)
async def search_category_name(message: Message, state: FSMContext) -> None:
    await state.update_data(name=message.text)
    await state.set_state(CategoryForm.cat_id)
    await message.answer("⌛ searching.")
    result = await request_item_list(url="category_list_1")
    item_list = result["result"]["resultList"]
    await state.clear()
    for i in item_list:
        msg, cat_title, number = category_info(i, message.text)
        if msg is not None:
            data = "cat_id_{}".format(number)
            print(f"{data = }")
            kb = InlineKeyboardMarkup(
                row_width=1,
                inline_keyboard=[
                    [
                        InlineKeyboardButton(text=cat_title, callback_data=data),
                    ]
                ],
            )
            await message.answer(**msg.as_kwargs(), reply_markup=kb)


@router.callback_query(F.data.startswith("cat_id"))
async def search_category_product_name(callback: CallbackQuery, state: FSMContext) -> None:
    print("cat_id=", callback.data)
    cat_id = str(callback.data).split('_')[2]
    print(f"{cat_id= }")
    await state.update_data(cat_id=int(cat_id))
    await state.set_state(CategoryForm.product)
    data = await state.get_data()
    print('#2', data.items())
    print('#3', data['cat_id'])
    await state.set_state(CategoryForm.product)
    path = os.path.join(settings.static_path, "category.png")
    await callback.message.answer_photo(photo=FSInputFile(path), caption="🛍️🛍🛍🛍🛍🛍 Введите название товара.")


@router.message(CategoryForm.cat_id)
async def search_category_sort(message: Message, state: FSMContext) -> None:
    await state.update_data(product=message.text)
    await state.set_state(CategoryForm.sort)
    data = await state.get_data()
    print('#4', data.items())
    path = os.path.join(settings.static_path, "category.png")
    await message.answer_photo(
        photo=FSInputFile(path),
        caption="Как отсортировать результат?",
        reply_markup=sort_keyboard
    )


@router.callback_query(CategoryForm.sort, F.data.in_(SORT_SET))
async def search_category_qnt(callback: CallbackQuery, state: FSMContext) -> None:
    await state.update_data(product=callback.data)
    await state.set_state(CategoryForm.qnt)
    data = await state.get_data()
    print('#5', data.items())
    path = os.path.join(settings.static_path, "category.png")
    photo = InputMediaPhoto(media=FSInputFile(path), caption="сколько единиц товара вывести?")
    await callback.message.edit_media(media=photo, reply_markup=await get_qnt_kb())


@router.callback_query(CategoryForm.qnt, F.data.in_(BTNS))
async def search_category_result(call: CallbackQuery, state: FSMContext) -> None:
    await state.update_data(qnt=call.data)
    data = await state.get_data()
    print('#6', data.items())
    search_data = dict()
    price_range_list = []
    try:
        await call.answer("⌛ searching {0}".format(data['product']))
        # for _ in range(ranges):
        #     await call.message.answer('🛍️ {0} товар'.format(_))
        result = await request_item_list(
            q=data["product"],
            sort=data["sort"],
            url="item_search_2",
            cat_id=data["cat_id"],
        )
        try:
            print("{0}\n❌ лимит бесплатных API превышен".format(result["message"]))
        except KeyError:
            pass
        ranges = int(data["qnt"])
        item_list = result["result"]["resultList"][:ranges]
        currency = result["result"]["settings"]["currency"]

        for item in item_list:
            msg, img = card_info(item, currency)
            kb = await item_kb(item["item"]["itemId"])
            price = item["item"]["sku"]["def"]["promotionPrice"]
            price_range_list.append(price)
            await call.message.answer_photo(photo=img, caption=msg, reply_markup=kb, parse_mode="HTML")

        search_data['user'] = call.from_user.id
        search_data['command'] = 'search'
        search_data["price_range"] = get_price_range(price_range_list)
        search_data['result_qnt'] = int(ranges)
        search_data['search_name'] = data['product']
        History().create(**search_data).save()  # todo make orm func for orm.py

        await state.clear()
    except AiogramError as err:
        await call.message.answer("⚠️ Ошибка\n{0}".format(str(err)))
