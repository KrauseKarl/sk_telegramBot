import typing as t

from aiogram import types
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from pydantic import ValidationError

from src.api_aliexpress import deserializers, request
from src.api_redis import RedisHandler
from src.api_telegram import CacheKey, MonitorAction, MonitorCBD, kbm
from src.api_telegram.keyboard.paginators import MonitorPaginationBtn
from src.core import config
from src.database import Favorite, History, Paginator, exceptions, orm
from src.utils import media

scheduler = AsyncIOScheduler()


class MonitorListManager:
    """Класс для работы со списком отслеживаемых товара."""
    def __init__(self, callback_data, user_id):
        self.user_id = user_id
        self.page = int(callback_data.page)
        self.navigate = callback_data.navigate
        self.array: t.Optional[list] = None
        self.len: t.Optional[int] = None
        self.item: t.Optional[dict] = None
        self.target: t.Optional[float] = None
        self.photo: t.Optional[types.InputMediaPhoto] = None
        self.empty_message = "⭕️ у вас пока нет отслеживаемых товаров"
        self.empty_image = "favorite"
        self.action = MonitorAction
        self.call_data = MonitorCBD
        self.kb_factory = MonitorPaginationBtn
        self.deserializer = deserializers.DeserializedHandler()

    async def _get_list(self) -> t.List[History]:
        """Получает список истории и сохраняет его в self.array."""
        if self.array is None:
            self.array = await orm.monitoring.get_list(self.user_id)
        return self.array

    async def _get_len(self) -> int:
        """Возвращает длину списка истории и сохраняет её в self.len."""
        if self.len is None:
            self.len = len(await self._get_list())
        return self.len

    async def _get_item(self) -> History:
        """Возвращает элемент истории для текущей страницы."""
        if self.item is None and await self._get_len() > 0:
            paginator = Paginator(await self._get_list(), page=self.page)
            self.item = paginator.get_page()[0]
        return self.item

    async def get_msg(self) -> str:
        """Возвращает сообщение для текущего элемента истории."""
        current_item = await self._get_item()
        return await self.deserializer.monitor(
            current_item, self.page, await self._get_len()
        )

    async def get_media(self) -> types.InputMediaPhoto:
        """
        Возвращает медиа (фото с подписью)
        для текущего элемента истории.
        """
        if self.photo is None:
            if await self._get_len() > 0:
                try:
                    current_item = await self._get_item()
                    self.photo = types.InputMediaPhoto(
                        media=current_item.image, caption=await self.get_msg()
                    )
                except (ValidationError, TypeError):
                    self.photo = await media.get_input_media_hero_image(
                        self.empty_image, await self.get_msg()
                    )
            else:
                self.photo = await media.get_input_media_hero_image(
                    self.empty_image, self.empty_message
                )
        return self.photo

    async def get_photo(self) -> t.Optional[str]:
        """Возвращает фото текущего элемента истории."""
        current_item = await self._get_item()
        return current_item.image if current_item else None

    async def get_keyboard(self):
        """Возвращает клавиатуру для пагинации."""
        if await self._get_len() >= 1:
            current_item = await self._get_item()
            kb = self.kb_factory(
                item_id=str(current_item.uid),
                action=self.action,
                call_data=self.call_data,
            )
            if await self._get_len() > 1:
                kb.create_pagination_buttons(
                    page=self.page,
                    navigate=self.navigate,
                    len_data=int(await self._get_len()),
                )
            kb.add_buttons(
                [
                    kb.graph_btn(self.navigate),
                    kb.delete_btn(self.navigate),
                    kb.target_btn(self.navigate),
                    kb.btn_text("menu"),
                ]
            ).add_markups([2, 1])
            return kb.create_kb()
        else:
            return await kbm.back()


class MonitorAddManager:
    """Класс для добавления товара в список отслеживаемых."""

    def __init__(self, callback_data, user_id):
        self.key = callback_data.key
        self.item_id = int(callback_data.item_id)
        self.page = callback_data.page
        self.user_id = user_id
        self.item: t.Optional[dict] = None
        self.deserializer = deserializers.DeserializedHandler()
        self.redis_handler = RedisHandler()

    async def _get_cache_key(self):
        """Возвращает ключ для поиска кэш-данных"""
        return CacheKey(key=self.key, api_page=self.page, extra="detail").pack()

    async def _get_item(self):
        """Возвращает данные об отслеживаемом товаре."""
        item_search = await orm.monitoring.get_item(self.item_id)
        if item_search:
            raise exceptions.CustomError(message="Товар уже отслеживается")
        cache_key = await self._get_cache_key()
        response = await self.redis_handler.get_data(cache_key)
        if response is None:
            response = await request.get_data_by_request_to_api(
                params={
                    "itemId": self.item_id,
                    "url": config.URL_API_ITEM_DETAIL,
                }
            )
        self.item = await self.deserializer.item_for_db(response, self.user_id)
        return self.item

    async def start_monitoring_item(self) -> None:
        """Создает экземпляр класса`ItemSearch`."""
        if self.item is None:
            self.item = await self._get_item()
        await orm.monitoring.create_item(self.item)


class MonitorDeleteManager:
    """Класс для удаления товара из списка отслеживаемых."""

    def __init__(self, callback_data, user_id):
        self.user_id = user_id
        self.page = int(callback_data.page)
        self.item_id = callback_data.item_id
        self.navigate = callback_data.navigate
        self.array: t.Optional[list] = None
        self.len: t.Optional[int] = None
        self.item: t.Optional[t.Dict[str, t.Any]] = None
        self.photo: t.Optional[types.InputMediaPhoto] = None
        self.empty_message: str = "⭕️ у вас нет отслеживаемых товаров"
        self.empty_image: str = "favorite"
        self.action = MonitorAction
        self.call_data = MonitorCBD
        self.kb_factory = MonitorPaginationBtn
        self.deserializer = deserializers.DeserializedHandler()

    async def _get_list(self) -> t.List[History]:
        """Получает список истории и сохраняет его в self.array."""
        if self.array is None:
            self.array = await orm.monitoring.get_list(self.user_id)
        return self.array

    async def stop_monitoring_item(self) -> None:
        """Удаляет экземпляр класса`ItemSearch` из БД."""
        await orm.monitoring.delete_item(self.item_id)

    async def _get_len(self) -> int:
        """
        Возвращает длину списка избранных товаров
        и сохраняет её в self.len.
        """
        if self.len is None:
            self.len = len(await self._get_list())
        return self.len

    async def _get_item(self) -> Favorite:
        """Возвращает элемент избранных товаров для текущей страницы."""

        if await self._get_len() > 0:
            if self.page > await self._get_len():
                self.page -= 1
            if self.page < 1:
                self.page = 1
            paginator = Paginator(await self._get_list(), page=self.page)
            self.item = paginator.get_page()[0]
        return self.item

    async def get_msg(self) -> str:
        """Возвращает сообщение для текущего элемента избранных товаров."""
        current_item = await self._get_item()
        return await self.deserializer.monitor(
            current_item, self.page, await self._get_len()
        )

    async def get_media(self) -> types.InputMediaPhoto:
        """
        Возвращает медиа (фото с подписью)
        для текущего элемента избранных товаров.
        """
        # if self.photo is None:
        if await self._get_len() > 0:
            try:
                current_item = await self._get_item()
                self.photo = types.InputMediaPhoto(
                    media=current_item.image, caption=await self.get_msg()
                )
            except (ValidationError, TypeError):
                self.photo = await media.get_input_media_hero_image(
                    self.empty_image, await self.get_msg()
                )
        else:
            self.photo = await media.get_input_media_hero_image(
                self.empty_image, self.empty_message
            )
        return self.photo

    async def get_photo(self) -> t.Optional[str]:
        """Возвращает фото текущего элемента истории."""
        current_item = await self._get_item()
        return current_item.image if current_item else None

    async def get_keyboard(self) -> types.InlineKeyboardMarkup:
        """Возвращает клавиатуру для пагинации."""

        paginator_length = await self._get_len()
        if paginator_length >= 1:
            current_item = await self._get_item()
            kb = self.kb_factory(
                item_id=str(current_item.uid),
                action=self.action,
                call_data=self.call_data,
            )
            if paginator_length > 1:
                kb.create_pagination_buttons(
                    page=self.page,
                    navigate=self.navigate,
                    len_data=int(await self._get_len()),
                )

            current_item = await self._get_item()
            if current_item:
                kb.add_buttons(
                    [
                        kb.graph_btn(self.navigate),
                        kb.delete_btn(self.navigate),
                        kb.btn_text("menu"),
                    ]
                ).add_markups([2, 1])

            return kb.create_kb()
        else:
            return await kbm.back()
