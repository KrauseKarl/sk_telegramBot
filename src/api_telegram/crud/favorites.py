from typing import Any, Dict, List, Optional

from aiogram import types as t
from peewee import IntegrityError
from pydantic import ValidationError

from src.api_aliexpress import deserializers as srz
from src.api_aliexpress import request
from src.api_redis.handlers import RedisHandler
from src.api_telegram import (
    CacheKey,
    DetailAction,
    FavoriteAction,
    FavoriteCBD,
    FavoriteDeleteCBD,
    FavoritePaginationBtn,
    ItemPaginationBtn,
    MonitorAction,
    MonitorCBD,
    kbm,
)
from src.api_telegram.crud.items import get_web_link
from src.core import config
from src.database import History, Paginator, models, orm
from src.utils import media


class FavoriteListManager:
    def __init__(self, callback_data, user_id):
        self.user_id = user_id
        self.page = int(callback_data.page)
        self.navigate = callback_data.navigate
        self.item_id = callback_data.item_id
        self.array: Optional[list] = None
        self.len: Optional[int] = None
        self.item: Optional[dict] = None
        self.photo: Optional[t.InputMediaPhoto] = None
        self.empty_message = "⭕️ у вас пока нет избранных товаров."
        self.empty_image: str = "favorite"
        self.action = FavoriteAction
        self.call_data = FavoriteCBD
        self.kb_factory = FavoritePaginationBtn
        self.deserializer = srz.DeserializedHandler()

    async def _get_favorite_list(self) -> List[History]:
        """Получает список истории и сохраняет его в self.array."""
        if self.array is None:
            self.array = await orm.favorite.get_list(self.user_id)
        return self.array

    async def _get_len(self) -> int:
        """Возвращает длину списка избранных товаров и сохраняет её в self.len."""
        if self.len is None:
            self.len = len(await self._get_favorite_list())
        return self.len

    async def _get_item(self) -> models.Favorite:
        """Возвращает элемент избранных товаров для текущей страницы."""
        try:
            if self.item is None and await self._get_len() > 0:
                paginator = Paginator(await self._get_favorite_list(), page=self.page)
                self.item = paginator.get_page()[0]
        except IndexError:
            paginator = Paginator(await self._get_favorite_list(), page=self.page - 1)
            self.item = paginator.get_page()[0]
        return self.item

    async def get_msg(self) -> str:
        """Возвращает сообщение для текущего элемента избранных товаров."""
        current_item = await self._get_item()
        return await self.deserializer.favorite(
            current_item, str(self.page), await self._get_len()
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
                    self.photo = t.InputMediaPhoto(
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

    async def get_photo(self) -> Optional[str]:
        """Возвращает фото текущего элемента истории."""
        current_item = await self._get_item()
        return current_item.image if current_item else None

    async def get_keyboard(self) -> t.InlineKeyboardMarkup:
        """Возвращает клавиатуру для пагинации."""
        current_item = await self._get_item()
        if await self._get_len() >= 1:
            kb = self.kb_factory(
                item_id=str(current_item.uid),
                action=self.action,
                call_data=self.call_data,
            )
            if await self._get_len() > 1:
                kb.create_pagination_buttons(
                    page=self.page,
                    navigate=self.navigate,
                    len_data=await self._get_len(),
                )
            is_monitoring = await orm.monitoring.get_item(str(current_item.product_id))
            if is_monitoring is None:
                data = MonitorCBD(
                    action=MonitorAction.add,
                    item_id=str(current_item.product_id),
                    page=self.page,
                ).pack()
                kb.add_button(kb.btn_data("price", data))
            kb.add_button(kb.delete_btn(self.navigate)).add_markup(2)
            kb.add_button(kb.btn_text("menu")).add_markup(2)
            return kb.create_kb()
        else:
            return await kbm.back()


class FavoriteAddManager:
    def __init__(self, callback_data, user_id):
        self.user_id = user_id

        self.data = callback_data
        self.action = callback_data.action
        self.page = int(callback_data.page)
        self.api_page = int(callback_data.api_page)
        self.response: Optional[dict] = None
        self.len: Optional[int] = None
        self.item: Optional[dict] = None
        self.already_exist_message = "⚠️ уже добавлено в избранное"
        self.empty_image: str = "favorite"

        self.call_data = FavoriteCBD
        self.kb_factory = FavoritePaginationBtn
        self.deserializer = srz.DeserializedHandler()
        self.redis_handler = RedisHandler()

    async def _is_favorite(self) -> bool:
        item_is_favorite = await orm.favorite.get_item(self.data.item_id)
        if item_is_favorite:
            raise IntegrityError("⚠️ уже добавлено в избранное")
        return bool(item_is_favorite)

    async def _request_data(self):
        _cache_key = CacheKey(
            key=self.data.key, api_page=self.page, extra="detail"
        ).pack()
        response = await self.redis_handler.get_data(_cache_key)
        if response is None:
            response = await request.request_api(
                params=dict(url=config.URL_API_ITEM_DETAIL, itemId=self.data.item_id)
            )

        return response

    async def _get_item_data(self):
        if not await self._is_favorite():
            if self.response is None:
                self.response = await self._request_data()
            self.item = await self.deserializer.item_for_db(self.response, self.user_id)
        return self.item

    async def add_to_favorites(self) -> None:
        if self.item is None:
            self.item = await self._get_item_data()
        await orm.favorite.get_or_create(self.item)

    async def get_item(self) -> Dict[str, Any]:
        return self.item

    async def keyboard(self) -> t.InlineKeyboardMarkup:
        kb = ItemPaginationBtn(
            key=self.data.key,
            api_page=self.data.api_page,
            paginator_len=int(self.data.last),
            item_id=self.data.item_id,
        )
        if self.action == FavoriteAction.detail:
            kb.add_buttons(
                [
                    kb.detail("back", self.page, DetailAction.go_view),
                    kb.btn_text("price"),
                ]
            ).add_markups([1, 2, 3])
        if self.action == FavoriteAction.list:
            data_web = ("url", await get_web_link(self.data.item_id))
            await kb.create_paginate_buttons(self.page)
            kb.add_buttons(
                [
                    kb.detail("view", self.page, DetailAction.go_view),
                    kb.btn_text("menu"),
                    kb.btn_data("web", data_web),
                ]
            ).add_markup(3)

        return kb.create_kb()

    async def message(self) -> t.InputMediaPhoto:
        item_data = await self._get_item_data()
        msg = "<b>{0:.50}</b>\n".format(item_data["title"])
        msg += "💰\t\tцена:\t\t<b>{0}</b> RUB\n".format(item_data["price"])
        msg += "👀\t\tзаказы:\t\t<b>{0}</b>\n".format(item_data["reviews"])
        msg += "🌐\t\t{0}\n\n".format(item_data["url"])
        msg += "<b>{0}</b> из {1} стр. {2}\t".format(
            self.page, self.data.last, self.api_page
        )
        is_favorite = await orm.favorite.get_item(self.data.item_id)
        if is_favorite:
            msg += "👍\tв избранном"
        return t.InputMediaPhoto(media=item_data["image"], caption=msg)


class FavoriteDeleteManager:
    def __init__(self, callback_data, user_id):
        self.user_id = user_id
        self.page = int(callback_data.page)
        self.item_id = callback_data.item_id
        self.navigate = callback_data.navigate
        self.array: Optional[list] = None
        self.len: Optional[int] = None
        self.item: Optional[dict] = None
        self.photo: Optional[t.InputMediaPhoto] = None
        self.empty_message = "⭕️ у вас пока нет избранных товаров."
        self.empty_image: str = "favorite"
        self.action = FavoriteAction
        self.call_data = FavoriteDeleteCBD
        self.kb_factory = FavoritePaginationBtn
        self.deserializer = srz.DeserializedHandler()

    async def _get_list(self) -> List[History]:
        """Получает список истории и сохраняет его в self.array."""

        if self.array is None:
            self.array = await orm.favorite.get_list(self.user_id)
        return self.array

    async def delete_from_favorites(self) -> None:
        await orm.favorite.delete(self.item_id)

    async def _get_len(self) -> int:
        """Возвращает длину списка избранных товаров и сохраняет её в self.len."""
        if self.len is None:
            self.len = len(await self._get_list())
        return self.len

    async def _get_item(self) -> models.Favorite:
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
        # print('get msg page =', self.page)
        return await self.deserializer.favorite(
            current_item, self.page, await self._get_len()
        )

    async def get_media(self) -> t.InputMediaPhoto:
        """
        Возвращает медиа (фото с подписью)
        для текущего элемента избранных товаров.
        """
        # if self.photo is None:
        if await self._get_len() > 0:
            try:
                current_item = await self._get_item()
                self.photo = t.InputMediaPhoto(
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

    async def get_photo(self) -> Optional[str]:
        """Возвращает фото текущего элемента истории."""
        current_item = await self._get_item()
        return current_item.image if current_item else None

    async def get_keyboard(self) -> t.InlineKeyboardMarkup:
        """Возвращает клавиатуру для пагинации."""
        current_item = await self._get_item()
        paginator_length = await self._get_len()
        if paginator_length >= 1:
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
                    [kb.delete_btn(self.navigate), kb.btn_text("menu")]
                ).add_markups([2, 2])
            return kb.create_kb()

        else:
            return await kbm.back()
