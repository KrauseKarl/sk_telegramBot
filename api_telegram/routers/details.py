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
redis_handler = RedisHandler()


# ITEM DETAIL ##########################################################################################################
@detail.callback_query(DetailCBD.filter(F.action.in_({DetailAction.go_view, DetailAction.back_detail})))
async def get_item_detail(
        call: CallbackQuery,
        callback_data: DetailCBD,
        state: FSMContext,

) -> None:
    try:
        await call.answer()
        cache_key = CacheKeyExtended(
            key=callback_data.key,
            api_page=callback_data.api_page,
            extra='detail',
            sub_page=callback_data.page
        ).pack()
        item_data = await redis_handler.get_data(cache_key)

        if item_data is None:
            params = dict(
                url=config.URL_API_ITEM_DETAIL,
                itemId=callback_data.item_id
            )
            item_data = await request_api(params)
            await redis_handler.set_data(key=cache_key, value=item_data)
        ############################################################
        item = await deserialize_item_detail(item_data, call.from_user.id)
        msg = await get_detail_info(item_data)
        item['command'] = 'detail'
        await orm_make_record_request(item)

        # todo refactor - add kb_factory
        kb = ItemPaginationBtn(
            key=callback_data.key,
            api_page=callback_data.api_page,
            item_id=callback_data.item_id,
            paginator_len=int(callback_data.last)
        )

        buttons = [
            kb.comment(callback_data.page),
            kb.images(callback_data.page),
            # kb.btn_text('price'),
            kb.detail('back', callback_data.page, DetailAction.back_list),
            kb.btn_data("price", f"item_search:{callback_data.item_id}"),

        ]
        is_favorite = await orm_get_favorite(item_id=callback_data.item_id)
        if is_favorite is None:
            buttons.insert(0, kb.favorite(callback_data.page))

        kb.add_buttons(buttons).add_markups([2, 2, 1])
        # todo refactor - add kb_factory

        ##################################################################
        for i in kb.get_kb():
            for k, v in i.items():
                # if v.startswith('ITD'):
                    print("💜 detail to list", v.split(":"))
        #################################################################

        await call.message.edit_media(
            media=InputMediaPhoto(
                media=item['image'],
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
    cache_key = CacheKeyExtended(key=key, api_page=api_page, extra='detail', sub_page=page).pack()
    item_img_cache = await redis_handler.get_data(cache_key)
    print(f"🟩 DATA FROM 💾CACHE [🖼 IMAGE]".rjust(20, "🟩"))

    if item_img_cache is None:
        response = await request_api(
            {
                "url": config.URL_API_REVIEW,
                "itemId": item_id
            }
        )
        item_img_cache = response['result']['item']
        print(f"🟥 DATA FROM 🌐INTERNET [🖼 IMAGE]".rjust(20, "🟥"))
        await redis_handler.set_data(key=cache_key, value=item_img_cache)
    # img_list = item_img_cache.get('images')

    img_list = item_img_cache['result']['item']['images']
    try:
        color_list = item_img_cache['result']['item']['description']['images']
        if isinstance(img_list, list):
            img_list.extend(color_list)
    except:
        pass
    print(f"🖼 1 img_list len = {len(img_list)=}")

    paginator = Paginator(array=img_list, page=int(img_page))
    img = paginator.get_page()[0]

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
