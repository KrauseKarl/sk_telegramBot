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
@detail.callback_query(F.data.startswith("item"))
async def get_item_detail(call: CallbackQuery, state: FSMContext) -> None:
    print('DETAIL ENDPOINT')
    try:
        await call.answer()
        item_id = str(call.data).split("_")[1]

        response = await request_api(
            url=config.URL_API_ITEM_DETAIL,
            item_id=item_id
        )

        item_data = await deserialize_item_detail(response, call.from_user.id)
        msg = await get_detail_info(response)
        await orm_make_record_request(item_data)

        media_group = MediaGroupBuilder()
        img_color = get_color_img(response)

        for img_set in img_color[:8]:
            media_group.add_photo(media=img_set)

        await call.message.answer_media_group(media=media_group.build())
        await state.clear()

        await state.set_state(FavoriteFSM.product_id)
        await state.update_data(product_id=item_id)

        await state.set_state(FavoriteFSM.title)
        await state.update_data(title=item_data["title"])

        await state.set_state(FavoriteFSM.price)
        await state.update_data(price=item_data["price"])

        await state.set_state(FavoriteFSM.reviews)
        await state.update_data(reviews=item_data["reviews"])

        await state.set_state(FavoriteFSM.stars)
        await state.update_data(stars=item_data["star"])

        await state.set_state(FavoriteFSM.url)
        await state.update_data(url=item_data["url"])

        await state.set_state(FavoriteFSM.image)
        await state.update_data(image=item_data["image"])

        img_qnt = len(img_color)
        fav_id = "favorite_add_{0}_{1}".format(item_id, img_qnt)
        # todo check if item already in favorites don not show fav button

        kb = await kb_builder(
            size=(1, 2, 2),
            data_list=[
                {"⭐️ добавить в избранное": fav_id},
                {"❌ закрыть": "delete_{0}_{1}".format(fav_id, img_qnt)},
                {"📉 отслеживать цену": "price"}
            ]
        )
        await call.message.answer(msg, reply_markup=kb)

    except FreeAPIExceededError as error:
        await call.answer(show_alert=True, text="⚠️ ОШИБКА\n\n{0}".format(error))
    except CustomError as error:
        msg, photo = await get_error_answer_photo(error)
        await call.message.answer_photo(
            photo=photo,
            caption=msg,
            reply_markup=await menu_kb()
        )