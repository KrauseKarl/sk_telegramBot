from aiogram import F, Router
from aiogram.types import CallbackQuery
from aiogram.utils.media_group import MediaGroupBuilder

from database.exceptions import CustomError
from request import *
from utils import *

detail = Router()


# ITEM DETAIL ##########################################################################################################
@detail.callback_query(F.data.startswith("item"))
async def get_item_detail(call: CallbackQuery) -> None:
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
            await call.message.answer_media_group(media=media_group.build(),  reply_markup=menu_kb)
            await call.message.answer('меню', reply_markup=menu_kb)
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
