from aiogram import types

from utils.media import get_fs_input_hero_image


async def get_review_image(
        review: dict = None,
        msg: str = "⭕️ нет комментариев"
):
    images = review.get('reviewImages', None)
    if images:
        media = ":".join(["https", images[0]])
    else:
        media = await get_fs_input_hero_image('not_found')
    photo = types.InputMediaPhoto(media=media, caption=msg)

    return photo
