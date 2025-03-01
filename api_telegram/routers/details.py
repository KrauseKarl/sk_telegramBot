from aiogram import F, Router
from aiogram.filters import or_f
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from aiogram.utils.media_group import MediaGroupBuilder

from api_aliexpress.deserializers import *
from api_aliexpress.request import *
from api_telegram.keyboards import *
from api_telegram.statments import *
from database.exceptions import *
from database.orm import *
from utils.message_info import *

detail = Router()


# ITEM DETAIL ##########################################################################################################
@detail.callback_query(DetailCBD.filter(F.action.in_({DetailAction.go_view, DetailAction.back_detail})))
async def get_item_detail(
        call: CallbackQuery,
        callback_data: DetailCBD,
        state: FSMContext,

) -> None:
    # print('🟦 DETAIL ENDPOINT')
    data = callback_data
    # print(data)
    try:
        await call.answer()
        cache_key = CacheKey(
            key=callback_data.key,
            api_page=callback_data.api_page,
            extra='detail',
            sub_key=callback_data.page
        ).pack()
        detail_cache = await redis_get_data_from_cache(cache_key)

        if detail_cache is None:
            # FAKE REQUEST TO FILE JSON ############################################
            path = os.path.join(
                config.BASE_DIR,
                FAKE_MAIN_FOLDER,
                DETAIL_FAKE_FOLDER,
                "detail_{0}.json".format(data.item_id)
            )
            my_file = Path(path)
            if my_file.is_file():
                print('request from 🟩 FILE')
                response = await request_api_detail_fake(item_id=data.item_id)
            else:
                print('request from 🟥 INTERNET')
                ######################################################################
                response = await request_api(
                    url=config.URL_API_ITEM_DETAIL,
                    item_id=data.item_id
                )
            detail_cache = response
            await redis_set_data_to_cache(key=cache_key, value=detail_cache)
        ############################################################
        item_data = await deserialize_item_detail(detail_cache, call.from_user.id)
        msg = await get_detail_info(detail_cache)
        await orm_make_record_request(item_data)

        # todo refactor - add kb_factory
        kb = ItemPaginationBtn(
            key=data.key,
            api_page=data.api_page,
            item_id=data.item_id,
            paginator_len=int(data.last)
        )
        is_favorite = await orm_get_favorite(item_id=data.item_id)
        buttons = [
            kb.detail('back', data.page, DetailAction.back_list),
            kb.comment(data.page),
            kb.images(data.page),
            kb.btn_text('price'),
        ]
        if is_favorite is None:
            buttons.insert(0, kb.favorite(data.page))
        (kb.add_buttons(buttons).add_markups([1, 2, 2]))
        for i in kb.get_kb():
            for k, v in i.items():
                if v.startswith('ITD'):
                    print("💜 detail to list", v.split(":"))
        # todo check if item already in favorites don not show fav button

        await call.message.edit_media(
            media=InputMediaPhoto(
                media=item_data['image'],
                caption=msg
            ),
            reply_markup=kb.create_kb()
        )
        # await call.message.answer(msg, reply_markup=kb)

    except FreeAPIExceededError as error:
        await call.answer(show_alert=True, text="⚠️ ОШИБКА\n\n{0}".format(error))
    except CustomError as error:
        msg, photo = await get_error_answer_photo(error)
        await call.message.answer_photo(
            photo=photo,
            caption=msg,
            reply_markup=await menu_kb()
        )


@detail.callback_query(ImageCBD.filter())
async def show_first_item_paginate_images(callback: CallbackQuery, callback_data: ImageCBD):
    item_id = callback_data.item_id
    page = int(callback_data.page)
    key = callback_data.key
    api_page = int(callback_data.api_page)
    navigate = callback_data.navigate
    img_page = int(callback_data.img_page)
    kb = ImgPaginationBtn(
        key=key,
        api_page=api_page,
        item_id=item_id,
        paginator_len=callback_data.last
    )
    cache_key = CacheKey(key=key, api_page=api_page, extra='detail', sub_key=page).pack()
    item_img_cache = await redis_get_data_from_cache(cache_key)
    # print(f"🔴🔴🔴CACHE")
    if item_img_cache is None:
        response = await request_api(
            url=config.URL_API_REVIEW,
            item_id=item_id,
        )
        item_img_cache = response['result']['item']
        # print(f"🟦🟦🟦INTERNET")
        await redis_set_data_to_cache(key=cache_key, value=item_img_cache)
    # img_list = item_img_cache.get('images')

    img_list = item_img_cache['result']['item']['images']
    try:
        color_list = item_img_cache['result']['item']['description']['images']
        if isinstance(img_list, list):
            img_list.extend(color_list)
    except:
        pass
    for i in img_list:
        print(f"-- {i}")
    print(f"🖼 1 img_list len = {len(img_list)=}")
    # print(f"🖼 2 {page= }")

    paginator = Paginator(array=img_list, page=int(img_page))
    img = paginator.get_page()[0]
    # print(f"🖼 3 {img= }")

    if paginator.len > 1:
        if navigate == ImgNavigation.first:
            kb.add_button(kb.next_btn(page, int(img_page) + 1)).add_markup(1)
        # if navigate == FavPagination.first:
        #     kb.add_button(kb.pg(page).next_btn(1)).add_markup(1)

        elif navigate == ImgNavigation.next:

            # kb.add_button(kb.pg(page).prev_btn(-1)).add_markup(1)
            kb.add_button(kb.prev_btn(page, int(img_page) - 1)).add_markup(2)
            if int(img_page) < paginator.len:
                kb.add_button(kb.next_btn(page, int(img_page) + 1)).add_markup(2)
                # kb.add_button(kb.pg(page).next_btn(1)).update_markup(2)

        elif navigate == ImgNavigation.prev:
            if int(img_page) > 1:
                kb.add_button(kb.prev_btn(page, int(img_page) - 1)).add_markup(2)
                # kb.add_button(kb.pg(page).prev_btn(-1)).update_markup(2)
            # kb.add_button(kb.pg(page).next_btn(1)).add_markup(1)
            kb.add_button(kb.next_btn(page, int(img_page) + 1)).add_markup(2)

    detail_button = kb.detail("back", page, DetailAction.back_detail)
    kb.add_button(detail_button).add_markups([1])

    try:
        msg = "{0} из {1}".format(img_page, paginator.len)
        media = InputMediaPhoto(media=":".join(["https", img]), caption=msg)
    except Exception as error:
        print(error.__dict__)
        media = await get_input_media_hero_image('error', str(error))

    for i in kb.get_kb():
        for k, v in i.items():
            if v.startswith('ITD'):
                print("💚 image to detail", v.split(":"))
    await callback.message.edit_media(media=media, reply_markup=kb.create_kb())
