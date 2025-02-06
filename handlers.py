import os.path
from typing import Union

from aiogram import F, Router, types
from aiogram.exceptions import AiogramError
from aiogram.filters import Command, CommandStart, or_f, Filter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, InputMediaPhoto
from peewee import IntegrityError
from pydantic import ValidationError
from aiogram.types.photo_size import PhotoSize

from database.orm import *
from keyboards import *
from pagination import *
from statments import *
from utils import *
from database.db import *
from config import *
from request import request_item_detail, request_item_list

router = Router()





@router.message(CommandStart())
async def start_command(message: Message) -> None:
    try:
        user = message.from_user
        welcome_msg = orm_get_or_create_user(user=user)
        await message.answer('{0}, {1}!'.format(welcome_msg, user.first_name))
    except Exception as error:
        await message.answer("⚠️ Произошла ошибка {0}".format(error))


# MENU #############################################################################################################
# @router.message(or_f(Command("menu"), F.data.startswith("menu")))
@router.message(CustomFilter('menu'))
async def menu(message: Message | CallbackQuery) -> None:
    photo_path = os.path.join(conf.static_path, "menu.png")
    if isinstance(message, CallbackQuery):
        await message.message.edit_media(
            media=InputMediaPhoto(media=FSInputFile(photo_path)),
            reply_markup=main_keyboard
        )
    else:
    # try:
        await message.answer_photo(
            photo=FSInputFile(photo_path),
            reply_markup=main_keyboard
        )
    # await message.answer(text='Главное меню', reply_markup=main_keyboard)
    # except Exception as error:
    #     await message.answer("⚠️ Произошла ошибка {0}".format(error))


# @router.callback_query()
# async def menu_call(callback: CallbackQuery) -> None:
#     try:
#         photo = InputMediaPhoto(
#             media=FSInputFile(os.path.join(conf.static_path, "menu.png")))
#         await callback.message.edit_media(media=photo, reply_markup=main_keyboard)
#     except Exception as err:
#         await callback.message.answer('⚠️ Что-то пошло не так с командой /menu')
#         await callback.message.answer(str(err))


# HISTORY #############################################################################################################
# @router.callback_query(or_f(Command("history"), F.data.startswith("history")))
@router.callback_query(CustomFilter('history'))
async def history_(call: Message | CallbackQuery) -> None:
    photo = FSInputFile(os.path.join(conf.static_path, "history.png"))
    print(type(call))
    if isinstance(call, CallbackQuery):
        message = call.message
        print('333 ', call.data)
        user_id = call.from_user.id
        print('345 ', call.from_user.id)

    else:
        message = call
        user_id = call.from_user.id
    print('555 ', message.text)

    history_list = await orm_get_history_list(user_id)

    kb = InlineKeyboardBuilder()
    if F.data.startswith("history"):
        page = 1
        call_back_data = "page_next_{0}".format(int(page) + 1)
        kb.add(InlineKeyboardButton(text='След. ▶', callback_data=call_back_data))
        kb.add(InlineKeyboardButton(text='главное меню', callback_data="menu"))
        paginator = Paginator(history_list, page=page)
        print(paginator.get_page())
        history_items = paginator.get_page()[0]
        msg = await history_info(history_items)
        msg = msg + "{0} из {1}".format(page, paginator.pages)
        photo = InputMediaPhoto(media=photo, caption=msg, parse_mode="HTML")
        await message.edit_media(media=photo, reply_markup=kb.adjust(1, 1).as_markup())


@router.callback_query(F.data.startswith("page"))
async def history_page(callback: Message | CallbackQuery) -> None:
    history_list = await orm_get_history_list(callback.from_user.id)
    keyboard = InlineKeyboardBuilder()

    page = int(callback.data.split("_")[2])
    paginator = Paginator(history_list, page=int(page))
    history_item = paginator.get_page()[0]
    msg = await history_info(history_item)
    msg = msg + "{0} из {1}".format(page, paginator.pages)
    if callback.data.startswith("page_next"):
        callback_previous = "page_previous_{0}".format(page - 1)
        keyboard.add(InlineKeyboardButton(text="◀ Пред.", callback_data=callback_previous))
        if page != paginator.pages:
            callback_next = "page_next_{0}".format(page + 1)
            keyboard.add(InlineKeyboardButton(text='След. ▶', callback_data=callback_next))
            # if paginator.pages > 10:
            #     callback_next = "page_next_{0}".format(page + 10)
            #     keyboard.add(InlineKeyboardButton(text='След. 10 ▶', callback_data=callback_next))
    elif callback.data.startswith("page_previous"):
        if page != 1:
            callback_previous = "page_previous_{0}".format(page - 1)
            keyboard.add(InlineKeyboardButton(text="◀ Пред.", callback_data=callback_previous))
            # if page > 10:
            #     callback_previous = "page_previous_{0}".format(page - 10)
            #     keyboard.add(InlineKeyboardButton(text="◀ Пред. 10", callback_data=callback_previous))
        callback_next = "page_next_{0}".format(page + 1)
        keyboard.add(InlineKeyboardButton(text='След. ▶', callback_data=callback_next))
    keyboard.add(InlineKeyboardButton(text='главное меню', callback_data="menu"))
    try:
        photo = types.InputMediaPhoto(media=history_item.image, caption=msg, show_caption_above_media=False)
    except ValidationError:
        media = FSInputFile(os.path.join(conf.static_path, "history.png"))
        photo = InputMediaPhoto(media=media, caption=msg, parse_mode='HTML')

        #
    await callback.message.edit_media(
        media=photo,
        reply_markup=keyboard.adjust(2, 2, 1).as_markup())


# ITEM LIST ############################################################################################################
# @router.callback_query(F.data.startswith("search"))
@router.callback_query(CustomFilter("search"))
async def search_name(call: CallbackQuery, state: FSMContext) -> None:
    print('call ', call.data)
    await state.set_state(Form.product)
    path = os.path.join(conf.static_path, "cart.png")
    photo = InputMediaPhoto(media=FSInputFile(path), caption="🛍️ Введите название товара.")
    await call.message.edit_media(media=photo)


@router.message(Form.product)
async def search_sort(message: Message, state: FSMContext) -> None:
    await state.update_data(product=message.text)
    await state.set_state(Form.sort)
    path = os.path.join(conf.static_path, "sort.png")
    await message.answer_photo(
        photo=FSInputFile(path),
        caption="Как отсортировать результат?",
        reply_markup=sort_keyboard
    )


@router.callback_query(Form.sort, F.data.in_(SORT_SET))
async def search_qnt(call: CallbackQuery, state: FSMContext) -> None:
    await state.update_data(sort=call.data)
    await state.set_state(Form.qnt)
    path = os.path.join(conf.static_path, "quantity.png")
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
async def get_item_detail(call: CallbackQuery) -> None:
    try:
        item_id = str(call.data).split("_")[1]
        response = await request_item_detail(item_id)
        item_data = await deserialize_item_detail(response, call.from_user.id)
        msg = await get_detail_info(response)
        msg = msg[:999] if len(msg) > 1000 else msg
        orm_make_record_detail(item_data)
        await call.message.answer_photo(photo=item_data['image'], caption=msg)

        img_color = get_color_img(response)
        if img_color is not None:
            image_color_list = separate_img_by_ten(img_color, 9)
            await call.message.answer("Количество цветов {0}".format(len(img_color)))
            for img_set in image_color_list:
                await call.message.answer_media_group(
                    media=[InputMediaPhoto(media=img) for img in img_set]
                )
        # images = detail_img(response)
        # if images is not None:
        #     image_color_list = list(separate_img_by_ten(images, 5))
        #     await call.message.answer("Все иллюстрации")
        #     for img in image_color_list:
        #         color_images = [types.InputMediaPhoto(media=i) for i in img]
        #         await call.message.answer_media_group(color_images, reply_markup=main_keyboard)
        await call.message.answer('меню', reply_markup=main_keyboard)
    except AiogramError as error:
        await call.message.answer("⚠️ Произошла ошибка{0}".format(error))


# CATEGORY  ###########################################################################################################
@router.callback_query(F.data.startswith("category"))
async def search_category(call: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(CategoryForm.name)
    path = os.path.join(conf.static_path, "category.png")
    photo = InputMediaPhoto(media=FSInputFile(path), caption="Введите название товара или категории?")
    await call.message.edit_media(media=photo)


@router.message(CategoryForm.name)
async def search_category_name(message: Message, state: FSMContext) -> None:
    await state.update_data(name=message.text)
    await state.set_state(CategoryForm.cat_id)
    await message.answer("⌛ searching <u>{0}</u>".format(message.text), parse_mode="HTML")
    result = await request_item_list(url="category_list_1")
    item_list = result["result"]["resultList"]
    # print(item_list)
    await state.clear()
    kb = InlineKeyboardBuilder()

    if len(item_list) > 0:
        count = 0
        for item in item_list:
            msg, cat_title, number, count = category_info(items=item, query=message.text)
            data = "cat_id_{}".format(number)
            if len(msg) > 2:
                button = InlineKeyboardButton(text="⭕️ {0}".format(cat_title), callback_data=data)
                kb.add(button)
            # kb = await kb_builder(size=(1,), data_list=[{cat_title: data}])
        await message.answer(
            "по запросу <u>{0}</u>\nнайдены следующие категории [{1}]".format(message.text, count),
            reply_markup=kb.adjust(*(2, 1, 1, 2)).as_markup(),
            parse_mode="HTML"
        )
    else:
        mgs = "⚠️По вашему запросу ничего не найдено.\nПопробуйте сформулировать запрос иначе."
        await message.answer(mgs, reply_markup=main_keyboard)


@router.callback_query(or_f(CategoryForm.cat_id, F.data.startswith("cat_id")))
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
    path = os.path.join(conf.static_path, "category.png")
    await callback.message.answer_photo(photo=FSInputFile(path), caption="🛍️🛍🛍🛍🛍🛍 Введите название товара.")


@router.message(CategoryForm.product)
async def search_category_sort(message: Message, state: FSMContext) -> None:
    await state.update_data(product=message.text)
    await state.set_state(CategoryForm.sort)
    data = await state.get_data()
    print('#4', data.items())
    path = os.path.join(conf.static_path, "category.png")
    await message.answer_photo(
        photo=FSInputFile(path),
        caption="Как отсортировать результат?",
        reply_markup=sort_keyboard
    )


@router.callback_query(CategoryForm.sort, F.data.in_(SORT_SET))
async def search_category_qnt(callback: CallbackQuery, state: FSMContext) -> None:
    await state.update_data(sort=callback.data)
    await state.set_state(CategoryForm.qnt)
    data = await state.get_data()
    print('#5', data.items())
    path = os.path.join(conf.static_path, "category.png")
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
