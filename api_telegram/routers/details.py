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
from utils.cache_key import get_extra_cache_key
from utils.message_info import *

detail = Router()
redis_handler = RedisHandler()


# ITEM DETAIL ##########################################################################################################
@detail.callback_query(DetailCBD.filter(F.action == DetailAction.go_view))
@detail.callback_query(DetailCBD.filter(F.action == DetailAction.back_detail))
async def get_item_detail(call: CallbackQuery, callback_data: DetailCBD) -> None:
    try:
        await call.answer()
        cache_key = CacheKeyExtended(
            key=callback_data.key,
            api_page=callback_data.api_page,
            extra='detail',
            sub_page=callback_data.page
        ).pack()
        # cache_key = await get_extra_cache_key(callback_data, 'detail')
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
        # item['command'] = 'detail'
        await orm_make_record_request(item)

        # todo refactor - add kb_factory_detailItem_page
        kb = ItemPaginationBtn(
            key=callback_data.key,
            api_page=callback_data.api_page,
            item_id=callback_data.item_id,
            paginator_len=int(callback_data.last)
        )

        kb.add_buttons([
            kb.comment(callback_data.page),
            kb.images(callback_data.page),
            # kb.btn_text('price'),
            kb.detail('back', callback_data.page, DetailAction.back_list),

        ])

        is_monitoring = await orm_get_monitoring_item(callback_data.item_id)
        if is_monitoring is None:
            data = MonitorCBD(
                action=MonitorAction.add,
                item_id=callback_data.item_id
            ).pack()
            kb.add_button(kb.btn_data("price", data))

        is_favorite = await orm_get_favorite(item_id=callback_data.item_id)
        if is_favorite is None:
            kb.add_button(kb.favorite(callback_data.page))

        kb.add_markups([2, 2, 1])
        # todo refactor - add kb_factory

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
    sub_page = int(callback_data.sub_page)

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

    paginator = Paginator(array=img_list, page=int(sub_page))
    img = paginator.get_page()[0]

    if paginator.len > 1:
        if navigate == Navigation.first:
            kb.add_button(kb.next_btn(page, int(sub_page) + 1)).add_markup(1)

        elif navigate == Navigation.next:

            kb.add_button(kb.prev_btn(page, int(sub_page) - 1)).add_markup(2)
            if int(sub_page) < paginator.len:
                kb.add_button(kb.next_btn(page, int(sub_page) + 1)).add_markup(2)

        elif navigate == Navigation.prev:
            if int(sub_page) > 1:
                kb.add_button(kb.prev_btn(page, int(sub_page) - 1)).add_markup(2)
            kb.add_button(kb.next_btn(page, int(sub_page) + 1)).add_markup(2)

    detail_button = kb.detail("back", page, DetailAction.back_detail)
    kb.add_button(detail_button).add_markups([1])

    try:
        msg = "{0} из {1}".format(sub_page, paginator.len)
        media = InputMediaPhoto(media=":".join(["https", img]), caption=msg)
    except Exception as error:
        print(error.__dict__)
        media = await get_input_media_hero_image('error', str(error))

    await callback.message.edit_media(media=media, reply_markup=kb.create_kb())
