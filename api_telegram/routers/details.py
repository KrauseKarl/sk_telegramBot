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
        callback_data: DetailCBD
) -> None:
    print('🟦 DETAIL ENDPOINT')
    try:
        await call.answer()

        response = await request_api(
            url=config.URL_API_ITEM_DETAIL,
            item_id=callback_data.item_id
        )
        print(f"🟦 {callback_data= }")
        item_data = await deserialize_item_detail(response, call.from_user.id)
        msg = await get_detail_info(response)
        await orm_make_record_request(item_data)

        # media_group = MediaGroupBuilder()
        # img_color = get_color_img(response)
        #
        # for img_set in img_color[:8]:
        #     media_group.add_photo(media=img_set)

        # await call.message.answer_media_group(media=media_group.build())

        # await state.clear()
        #
        # await state.set_state(FavoriteFSM.product_id)
        # await state.update_data(product_id=item_id)
        #
        # await state.set_state(FavoriteFSM.title)
        # await state.update_data(title=item_data["title"])
        #
        # await state.set_state(FavoriteFSM.price)
        # await state.update_data(price=item_data["price"])
        #
        # await state.set_state(FavoriteFSM.reviews)
        # await state.update_data(reviews=item_data["reviews"])
        #
        # await state.set_state(FavoriteFSM.stars)
        # await state.update_data(stars=item_data["star"])
        #
        # await state.set_state(FavoriteFSM.url)
        # await state.update_data(url=item_data["url"])
        #
        # await state.set_state(FavoriteFSM.image)
        # await state.update_data(image=item_data["image"])

        add_favorite = FavoriteAddCBD(
            action=FavAction.detail,
            item_id=callback_data.item_id,
            key=callback_data.key,
            api_page=callback_data.api_page,
            page=callback_data.page,
            next=callback_data.next,
            prev=callback_data.prev,
            first=callback_data.first,
            last=callback_data.last,
        ).pack()
        back_to_list = DetailCBD(
            action=DetailAction.back,
            item_id=callback_data.item_id,
            key=callback_data.key,
            api_page=callback_data.api_page,
            page=callback_data.page,
            next=callback_data.next,
            prev=callback_data.prev,
            first=callback_data.first,
            last=callback_data.last,
        ).pack()
        # todo check if item already in favorites don not show fav button

        kb = await kb_builder(
            size=(1, 2, 2),
            data_list=[
                {"⭐️ добавить в избранное": add_favorite},
                {"🔙 назад": back_to_list},
                {"📉 отслеживать цену": "price"}
            ]
        )
        await call.message.edit_media(
            media=InputMediaPhoto(
                media=item_data['image'],
                caption=msg
            ),
            reply_markup=kb
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
