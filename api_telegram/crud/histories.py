import os
from typing import List

from aiogram import types
from pydantic import ValidationError

from api_telegram.keyboards import kb_builder
from core import config
from database.models import History
from database.orm import orm_get_history_list
from database.pagination import Paginator
from utils.media import get_fs_input_hero_image
from utils.message_info import history_info


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


async def make_paginate_history_list(
        history_list: List[History], page: int = 1
):
    if len(history_list) == 0:
        msg = "⭕️у вас нет истории просмотров"
        kb = await kb_builder(
            size=(1,),
            data_list=[
                {"🏠 назад": "menu"}
            ]
        )
        return msg, kb, None

    kb = await kb_builder(
        size=(1,),
        data_list=[
            {"След. ▶": "page_fav_next_{0}".format(int(page) + 1)},
            {"🏠 меню": "menu"},
        ]
    )

    paginator = Paginator(history_list, page=page)
    one_items = paginator.get_page()[0]
    msg = await history_info(one_items)
    msg = msg + "\n{0} из {1}".format(page, paginator.pages)

    return msg, kb, one_items.image

