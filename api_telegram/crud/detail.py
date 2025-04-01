from typing import Optional

from aiogram.types import InputMediaPhoto, InlineKeyboardMarkup

from api_aliexpress import request_api
from api_aliexpress.deserializers import DeserializedHandler
from api_redis import RedisHandler
from api_telegram import (
    DetailAction,
    MonitorCBD,
    MonitorAction,
    ItemPaginationBtn,
    DetailCBD,
    CacheKeyExtended, CacheKey
)
from core import config
from database import orm_make_record_request, orm_get_monitoring_item, orm_get_favorite


class DetailManager:
    def __init__(self, callback_data, user_id):
        self.user_id: int = user_id
        self.key: str = callback_data.key
        self.item_id = callback_data.item_id
        self.api_page: str = callback_data.api_page
        self.page: int = int(callback_data.page)
        self.last: int = int(callback_data.last)
        self.item: dict = dict()
        self.response: Optional[dict] = None
        self.cache_key = None
        self.action = DetailAction
        self.call_data = DetailCBD
        self.kb_factory = ItemPaginationBtn
        self.redis_handler = RedisHandler()
        self.deserializer = DeserializedHandler()

    async def _get_cache_key(self):
        """Получает ключ для поиска кэша."""
        return CacheKey(
            key=self.key,
            api_page=self.page,
            extra='detail'
        ).pack()

    async def _request_data(self):
        params = dict(
            url=config.URL_API_ITEM_DETAIL,
            itemId=self.item_id
        )
        return await request_api(params)

    async def _get_item_info(self):
        """Получает список истории и сохраняет его в self.array."""
        if self.response is None:
            if self.cache_key is None:
                self.cache_key = await self._get_cache_key()
            print(f'detail cache key {self.cache_key}')
            item_data = await self.redis_handler.get_data(self.cache_key)
            if item_data is None:
                item_data = await self._request_data()

            if item_data is not None:
                await self.redis_handler.set_data(
                    key=self.cache_key,
                    value=item_data
                )
                self.response = item_data

        return self.response

    async def get_msg(self) -> str:
        """Возвращает сообщение с подробной информацией о товаре."""
        if self.response is None:
            self.response = await self._get_item_info()
        self.item = await self.deserializer.item_for_db(
            self.response,
            self.user_id
        )
        await orm_make_record_request(self.item)
        return await self.deserializer.item_detail(self.response)

    async def get_media(self):
        msg = await self.get_msg()
        return InputMediaPhoto(
            media=self.item.get('image', None),
            caption=msg
        )

    async def get_keyboard(self) -> InlineKeyboardMarkup:
        """Возвращает клавиатуру."""
        kb = ItemPaginationBtn(
            key=self.key,
            api_page=int(self.api_page),
            item_id=self.item_id,
            paginator_len=int(self.last)
        )
        kb.add_buttons([
            kb.comment(self.page),
            kb.images(self.page),
            kb.detail('back', self.page, DetailAction.back_list),
        ])
        is_monitoring = await orm_get_monitoring_item(self.item_id)
        if is_monitoring is None:
            data = MonitorCBD(
                action=MonitorAction.add,
                item_id=self.item_id
            ).pack()
            kb.add_button(kb.btn_data("price", data))
        is_favorite = await orm_get_favorite(item_id=self.item_id)
        if is_favorite is None:
            kb.add_button(kb.favorite(self.page))
        kb.add_markups([2, 2, 1])

        return kb.create_kb()
