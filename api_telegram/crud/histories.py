from typing import Optional, List

from aiogram import types as t
from aiogram.types import InputMediaPhoto
from pydantic import ValidationError

from api_telegram.callback_data import HistoryAction, HistoryCBD
from api_telegram.keyboard.builders import kbm
from api_telegram.keyboard.paginators import HistoryPaginationBtn
from database.models import History
from database.orm import orm_get_history_list
from database.paginator import Paginator
from utils.media import get_input_media_hero_image
from utils.message_info import history_info


class HistoryManager:
    def __init__(self, callback_data, user_id):
        self.user_id = user_id
        self.page = int(callback_data.page)
        self.navigate = callback_data.navigate
        self.array: Optional[list] = None
        self.len: Optional[int] = None
        self.item: Optional[dict] = None
        self.photo: Optional[t.InputMediaPhoto] = None
        self.empty_message = "⭕️ история просмотра пуста."
        self.empty_image = "history"
        self.action = HistoryAction
        self.call_data = HistoryCBD
        self.kb_factory = HistoryPaginationBtn

    async def _get_history_list(self) -> List[History]:
        """Получает список истории и сохраняет его в self.array."""
        if self.array is None:
            self.array = await orm_get_history_list(self.user_id)
        return self.array

    async def _get_len(self) -> int:
        """Возвращает длину списка истории и сохраняет её в self.len."""
        if self.len is None:
            self.len = len(await self._get_history_list())
        return self.len

    async def _get_item(self) -> History:
        """Возвращает элемент истории для текущей страницы."""
        if self.item is None and await self._get_len() > 0:
            paginator = Paginator(await self._get_history_list(), page=self.page)
            self.item = paginator.get_page()[0]
        return self.item

    async def get_msg(self) -> str:
        """Возвращает сообщение для текущего элемента истории."""
        current_item = await self._get_item()
        return await history_info(current_item, str(self.page), await self._get_len())

    async def get_media(self) -> InputMediaPhoto:
        """Возвращает медиа (фото с подписью) для текущего элемента истории."""
        if self.photo is None:
            if await self._get_len() > 0:
                try:
                    current_item = await self._get_item()
                    self.photo = t.InputMediaPhoto(
                        media=current_item.image,
                        caption=await self.get_msg()
                    )
                except (ValidationError, TypeError):
                    self.photo = await get_input_media_hero_image(
                        self.empty_image,
                        await self.get_msg()
                    )
            else:
                self.photo = await get_input_media_hero_image(
                    self.empty_image,
                    self.empty_message
                )
        return self.photo

    async def get_photo(self) -> Optional[str]:
        """Возвращает фото текущего элемента истории."""
        current_item = await self._get_item()
        return current_item.image if current_item else None

    async def get_keyboard(self):
        """Возвращает клавиатуру для пагинации."""
        if await self._get_len() >= 1:
            kb = self.kb_factory(
                action=self.action,
                call_data=self.call_data
            )
            kb.create_pagination_buttons(
                page=self.page,
                navigate=self.navigate,
                len_data=int(await self._get_len())
            )
            kb.add_button(kb.btn_text('menu')).add_markup(1)
            return kb.create_kb()
        else:
            return await kbm.back()
