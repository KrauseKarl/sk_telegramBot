from aiogram import F, Router
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
@detail.callback_query(DetailCBD.filter(F.action == DetailAction.view))
async def get_item_detail(
        call: CallbackQuery,
        state: FSMContext,
        data: DetailCBD
) -> None:
    print('🟦 DETAIL ENDPOINT')
    try:
        await call.answer()
        response = await request_api(
            url=config.URL_API_ITEM_DETAIL,
            item_id=data.item_id
        )
        item_data = await deserialize_item_detail(response, call.from_user.id)
        msg = await get_detail_info(response)
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
            kb.detail('back', data.page, DetailAction.back),
            kb.btn_text('price')
        ]
        if is_favorite is None:
            buttons.insert(0, kb.favorite(data.page))
        (kb.add_buttons(buttons).add_markups([1, 2, 2]))

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
