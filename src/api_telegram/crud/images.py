from typing import Optional

from aiogram.types import InlineKeyboardMarkup, InputMediaPhoto
from pydantic import ValidationError

from src.api_aliexpress.request import request_api
from src.api_redis.handlers import RedisHandler
from src.api_telegram import (
    CacheKey,
    DetailAction,
    ImageCBD,
    ImagePaginationBtn,
    ImagesAction,
    kbm,
)
from src.core import config
from src.database.paginator import Paginator
from src.utils import media


class ImageManager:
    def __init__(self, callback_data, user_id):
        self.user_id: int = user_id
        self.key: str = callback_data.key
        self.page: int = int(callback_data.page)
        self.api_page = str(callback_data.api_page)
        self.navigate: str = callback_data.navigate
        self.sub_page: int = int(callback_data.sub_page)
        self.item_id = callback_data.item_id
        self.extra = "detail"
        self.array: Optional[list] = None
        self.len: Optional[int] = None
        self.item: Optional[dict] = None
        self.photo: Optional[InputMediaPhoto] = None

        self.empty_message: str = "⭕️ изображения отсутствуют"
        self.empty_image: str = "not_found"
        self.action = ImagesAction
        self.call_data = ImageCBD
        self.kb_factory = ImagePaginationBtn
        self.redis_handler = RedisHandler()

    async def _get_cache_key(self):
        """Получает ключ для поиска кэша."""
        return CacheKey(key=self.key, api_page=self.page, extra="detail").pack()

    async def _request_data(self):
        data = dict(
            url=config.URL_API_ITEM_DETAIL,
            itemId=self.item_id,
        )
        return await request_api(data)

    async def _get_list(self):
        """Получает список изображений и сохраняет его в self.array."""
        if self.array is None:
            cache_key = await self._get_cache_key()
            print(f"IMAGE  {cache_key= }")
            item_img_cache = await self.redis_handler.get_data(cache_key)
            if item_img_cache is None:
                item_img_cache = await self._request_data()
                if item_img_cache is not None:
                    await self.redis_handler.set_data(
                        key=cache_key, value=item_img_cache
                    )
            item_response = item_img_cache.get("result").get("item")
            images = item_response.get("images")
            colors_image = item_response.get("description").get("images")
            if colors_image:
                images.extend(colors_image)
            self.array = images
        return self.array

    async def _get_len(self) -> int:
        """Возвращает длину списка изображений товара и сохраняет её в self.len."""
        if self.len is None:
            self.len = len(await self._get_list())
        return self.len

    async def _get_item(self):
        """Возвращает элемент изображений товара для текущей страницы."""

        if self.item is None and await self._get_len() > 0:
            paginator = Paginator(await self._get_list(), page=self.sub_page)
            self.item = paginator.get_page()[0]
        return self.item

    async def get_msg(self) -> str:
        """Возвращает сообщение для текущего элемента изображений товара."""
        return "{0} из {1}".format(self.sub_page, self.len)

    async def get_media(self) -> InputMediaPhoto:
        """
        Возвращает медиа (фото с подписью)
        для текущего элемента избранных товаров.
        """
        if self.photo is None:
            if await self._get_len() > 0:
                try:
                    current_img = await self._get_item()
                    self.photo = InputMediaPhoto(
                        media=":".join(["https", current_img]),
                        caption=await self.get_msg(),
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

    async def get_keyboard(self) -> InlineKeyboardMarkup:
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
