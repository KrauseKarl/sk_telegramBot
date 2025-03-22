from typing import Optional
from aiogram.types import InputMediaPhoto, InlineKeyboardMarkup
from pydantic import ValidationError

from api_aliexpress.request import request_api_review
from api_redis.handlers import RedisHandler
from api_telegram.callback_data import (
    ReviewCBD,
    ReviewAction,
    CacheKeyExtended,
    DetailAction
)
from api_telegram.keyboard.builders import kbm
from api_telegram.keyboards import ReviewPaginationBtn
from core import config
from database.paginator import Paginator
from utils.media import get_input_media_hero_image
from utils.message_info import create_review_tg_answer


class ReviewManager:
    def __init__(self, callback_data, user_id):
        self.user_id: int = user_id
        self.page: int = int(callback_data.page)
        self.navigate: str = callback_data.navigate
        self.key: str = callback_data.key
        self.item_id = callback_data.item_id
        self.api_page: str = callback_data.api_page
        self.sub_page: int = int(callback_data.sub_page)
        self.array: Optional[list] = None
        self.len: Optional[int] = None
        self.item: Optional[dict] = None
        self.photo: Optional[InputMediaPhoto] = None
        self.empty_message: str = "⭕️ нет комментариев"
        self.empty_image: str = "not_found"
        self.action = ReviewAction
        self.call_data = ReviewCBD
        self.kb_factory = ReviewPaginationBtn
        self.redis_handler = RedisHandler()

    async def _get_cache_key(self):
        """Получает ключ для поиска кэша."""
        return CacheKeyExtended(
            key=self.key,
            api_page=self.api_page,
            sub_page=self.sub_page,
            extra='review'
        ).pack()

    async def _request_data(self):
        data = dict(
            url=config.URL_API_REVIEW,
            page=str(self.api_page),
            itemId=self.item_id,
            sort="latest",
            filters="allReviews"
        )
        response = await request_api_review(data)
        return response.get('result').get('resultList', None)

    async def _get_review_list(self):
        """Получает список истории и сохраняет его в self.array."""
        if self.array is None:
            cache_key = await self._get_cache_key()
            review_list = await self.redis_handler.get_data(cache_key)
            if review_list is None:
                review_list = await self._request_data()
            if review_list is not None:
                await self.redis_handler.set_data(key=cache_key, value=review_list)
                self.array = review_list
        return self.array

    async def _get_len(self) -> int:
        """Возвращает длину списка избранных товаров и сохраняет её в self.len."""
        if self.len is None:
            self.len = len(await self._get_review_list())
        return self.len

    async def _get_item(self):
        """Возвращает элемент избранных товаров для текущей страницы."""
        print(f"\n{len(self.array)= }\n")
        if self.item is None and await self._get_len() > 0:
            paginator = Paginator(await self._get_review_list(), page=self.sub_page)
            self.item = paginator.get_page()[0]
        return self.item

    async def get_msg(self) -> str:
        """Возвращает сообщение для текущего элемента избранных товаров."""
        current_item = await self._get_item()
        return await create_review_tg_answer(
            current_item, str(self.sub_page), await self._get_len()
        )

    async def get_media(self) -> InputMediaPhoto:
        """Возвращает медиа (фото с подписью) для текущего элемента избранных товаров."""
        if self.photo is None:
            if await self._get_len() > 0:
                try:
                    current_item = await self._get_item()
                    images = current_item.get('reviewImages', None)
                    media = ":".join(["https", images[0]])
                    self.photo = InputMediaPhoto(
                        media=media,
                        caption=await self.get_msg()
                    )
                except (ValidationError, TypeError, KeyError):
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
        images = current_item.get('reviewImages', None)
        media = ":".join(["https", images[0]])
        return media if images else None

    async def get_keyboard(self) -> InlineKeyboardMarkup:
        """Возвращает клавиатуру для пагинации."""
        if await self._get_len() >= 1:
            kb = self.kb_factory(
                action=self.action,
                call_data=self.call_data,
                item_id=self.item_id,
                key=self.key,
                api_page=self.api_page,
                paginator_len=await self._get_len()
            )
            if await self._get_len() >= 1:
                kb.create_pagination_buttons(
                    page=int(self.page),
                    navigate=self.navigate,
                    len_data=await self._get_len(),
                    sub_page=int(self.sub_page)
                )
            extra_buttons = [
                kb.detail("back", self.page, DetailAction.back_detail)
            ]
            kb.add_buttons(extra_buttons).add_markups([1])
            return kb.create_kb()
        else:
            return await kbm.back()
