import os

from aiogram import types
from pydantic import ValidationError

from core import config
from database.orm import orm_get_history_list
from database.pagination import make_paginate_history_list
from utils.media import get_fs_input_hero_image


async def get_history_message(user_id: str | int) -> tuple:
    """

    :param user_id:
    :return:
    """
    history_list = await orm_get_history_list(user_id)
    msg, kb, img = await make_paginate_history_list(history_list)
    try:
        photo = types.FSInputFile(path=os.path.join(config.IMAGE_PATH, img))
    except (ValidationError, TypeError):
        photo = await get_fs_input_hero_image("history")

    return msg, kb, photo
