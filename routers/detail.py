from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from aiogram.utils.media_group import MediaGroupBuilder

from database.exceptions import CustomError
from keyboards import kb_builder
from request import *
from statments import FavoriteForm
from utils import *

detail = Router()


# ITEM DETAIL ##########################################################################################################
@detail.callback_query(F.data.startswith("item"))
async def get_item_detail(call: CallbackQuery, state: FSMContext) -> None:
    try:

        item_id = str(call.data).split("_")[1]
        response = await request_item_detail(item_id)
        item_data = await deserialize_item_detail(response, call.from_user.id)
        msg = await get_detail_info(response)
        await orm_make_record_request(item_data)
        # await call.message.edit_media(
        #     media=InputMediaPhoto(media=item_data['image'], caption=msg),
        #     reply_markup=menu_kb
        # )
        # media_group = MediaGroupBuilder(caption="Media group caption")
        # # Add photo
        # media_group.add_photo(media="https://picsum.photos/200/300")
        # # Dynamically add photo with known type without using separate method
        # media_group.add(type="photo", media="https://picsum.photos/200/300")
        # # ... or video
        # media_group.add(type="video", media=FSInputFile("media/video.mp4"))

        media_group = MediaGroupBuilder(caption=msg)
        # COLOR IMAGE
        img_color = get_color_img(response)
        # last_img = img_color[-1]
        # media = []
        if img_color is not None:
            print(len(img_color[:8]))
            # image_color_list = separate_img_by_ten(img_color, 9)
            # await call.message.answer("Количество цветов {0}".format(len(img_color)))
            for img_set in img_color[:8]:
                media_group.add_photo(media=img_set)
                # media = [InputMediaPhoto(media=img) for img in img_set]
            # media.append(InputMediaPhoto(media=last_img, caption=msg))
            await call.message.answer_media_group(
                media=media_group.build(),
                reply_markup=menu_kb
            )
            await state.clear()

            await state.set_state(FavoriteForm.product_id)
            await state.update_data(product_id=item_id)

            await state.set_state(FavoriteForm.title)
            await state.update_data(title=item_data["title"])

            await state.set_state(FavoriteForm.price)
            await state.update_data(price=item_data["price"])

            await state.set_state(FavoriteForm.reviews)
            await state.update_data(reviews=item_data["reviews"])

            await state.set_state(FavoriteForm.stars)
            await state.update_data(stars=item_data["star"])

            await state.set_state(FavoriteForm.url)
            await state.update_data(url=item_data["url"])

            await state.set_state(FavoriteForm.image)
            await state.update_data(image=item_data["image"])

            kb = await kb_builder(
                size=(1,),
                data_list=[{"добавить в избранное": "favorite_add_{}".format(item_id)}]
            )
            await call.message.answer('избранное', reply_markup=kb)
            # await call.message.answer('меню', reply_markup=menu_kb)
        # else:
        # # ALL IMAGE
        #     images = detail_img(response)
        #     if images is not None:
        #         image_color_list = list(separate_img_by_ten(images, 5))
        #         await call.message.answer("Все иллюстрации")
        #         for img in image_color_list:
        #             color_images = [InputMediaPhoto(media=i) for i in img]
        #             await call.message.answer_media_group(color_images, reply_markup=menu_kb)
        # await call.message.answer('меню', reply_markup=menu_kb)
    except CustomError as error:
        msg, photo = await get_error_answer_photo(error)
        await call.message.answer_photo(
            photo=photo,
            caption=msg,
            reply_markup=menu_kb
        )
