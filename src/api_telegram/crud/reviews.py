from typing import Optional

from aiogram import types as t
from pydantic import ValidationError

from src.api_aliexpress import DeserializedHandler, request_api
from src.api_redis.handlers import RedisHandler
from src.api_telegram import (
    DetailAction,
    ReviewAction,
    ReviewCBD,
    ReviewPaginationBtn,
    kbm,
)
from src.core import config
from src.database import Paginator
from src.utils import cache_key, media


class ReviewManager:
    def __init__(self, callback_data, user_id):
        self.user_id: int = user_id
        self.callback_data = callback_data
        self.page: int = int(callback_data.page)
        self.navigate: str = callback_data.navigate
        self.key: str = callback_data.key
        self.item_id = callback_data.item_id
        self.api_page: str = callback_data.api_page
        self.sub_page: int = int(callback_data.sub_page)
        self.extra = "detail"
        self.array: Optional[list] = None
        self.len: Optional[int] = None
        self.item: Optional[dict] = None
        self.photo: Optional[t.InputMediaPhoto] = None

        self.empty_message: str = "⭕️ нет комментариев"
        self.empty_image: str = "not_found"

        self.action = ReviewAction
        self.call_data = ReviewCBD
        self.kb_factory = ReviewPaginationBtn
        self.redis_handler = RedisHandler()
        self.deserializer = DeserializedHandler()
        self.key_handler = cache_key.CacheKeyManager()

    async def _request_data(self):
        data = dict(
            url=config.URL_API_REVIEW,
            page=str(self.api_page),
            itemId=self.item_id,
            sort="hasImage",
            filters="allReviews",
        )
        response = await request_api(data)
        return response.get("result").get("resultList", None)

    async def _get_review_list(self):
        """Получает список истории и сохраняет его в self.array."""
        if self.array is None:
            current_cache_key = await self.key_handler.generate_review_key(
                self.callback_data, self.extra
            )
            review_list = await self.redis_handler.get_data(current_cache_key)
            if review_list is None:
                review_list = await self._request_data()
                if review_list is not None:
                    await self.redis_handler.set_data(
                        key=current_cache_key, value=review_list
                    )
            self.array = review_list
        return self.array

    async def _get_len(self) -> int:
        """Возвращает длину списка избранных товаров и сохраняет её в self.len."""
        if self.len is None:
            self.len = len(await self._get_review_list())
        return self.len

    async def _get_item(self):
        """Возвращает элемент избранных товаров для текущей страницы."""
        if self.item is None and await self._get_len() > 0:
            paginator = Paginator(await self._get_review_list(), page=self.sub_page)
            self.item = paginator.get_page()[0]
        return self.item

    async def get_msg(self) -> str:
        """Возвращает сообщение для текущего элемента избранных товаров."""
        current_item = await self._get_item()
        return await self.deserializer.reviews(
            current_item, str(self.sub_page), await self._get_len()
        )

    async def get_media(self) -> t.InputMediaPhoto:
        """
        Возвращает медиа (фото с подписью)
        для текущего элемента избранных товаров.
        """
        if self.photo is None:
            if await self._get_len() > 0:
                try:
                    current_item = await self._get_item()
                    images = current_item.get("review").get("reviewImages", None)
                    img = ":".join(["https", images[0]])
                    self.photo = t.InputMediaPhoto(
                        media=img, caption=await self.get_msg()
                    )
                except (ValidationError, TypeError, KeyError):
                    self.photo = await media.get_input_media_hero_image(
                        self.empty_image, await self.get_msg()
                    )
            else:
                self.photo = await media.get_input_media_hero_image(
                    self.empty_image, self.empty_message
                )
        return self.photo

    async def get_photo(self) -> Optional[str]:
        """Возвращает фото текущего элемента истории."""
        current_item = await self._get_item()
        images = current_item.get("reviewImages", None)
        img = ":".join(["https", images[0]])
        return img if images else None

    async def get_keyboard(self) -> t.InlineKeyboardMarkup:
        """Возвращает клавиатуру для пагинации."""
        if await self._get_len() >= 1:
            kb = self.kb_factory(
                action=self.action,
                call_data=self.call_data,
                item_id=self.item_id,
                key=self.key,
                api_page=self.api_page,
                paginator_len=await self._get_len(),
            )
            if await self._get_len() >= 1:
                kb.create_pagination_buttons(
                    page=int(self.page),
                    navigate=self.navigate,
                    len_data=await self._get_len(),
                    sub_page=int(self.sub_page),
                )
            extra_buttons = [kb.detail("back", self.page, DetailAction.back_detail)]
            kb.add_buttons(extra_buttons).add_markups([1])
            return kb.create_kb()
        else:
            return await kbm.back()
