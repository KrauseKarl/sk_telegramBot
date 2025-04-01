from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InputMediaPhoto
from pydantic import ValidationError

from api_aliexpress.deserializers import *
from api_aliexpress.request import *
from api_telegram.crud.items import get_web_link
from api_telegram.keyboard.paginators import *
from api_telegram import *
from core import config
from database import (
    orm_get_favorite_list,
    orm_get_favorite,
    orm_delete_favorite,
    orm_get_or_create_favorite,
    History,
    Paginator
)

deserializer = DeserializedHandler()


async def delete_favorite_instance(item_id: str) -> bool:
    favorite_obj = await orm_get_favorite(item_id)
    # await delete_img_from_static(favorite_obj)
    try:
        await orm_delete_favorite(item_id)
        return True
    except Exception as error:
        print("delete error = ", error)
        return False


class FavoriteListManager:
    def __init__(self, callback_data, user_id):
        self.user_id = user_id
        self.page = int(callback_data.page)
        self.navigate = callback_data.navigate
        self.array: Optional[list] = None
        self.len: Optional[int] = None
        self.item: Optional[dict] = None
        self.photo: Optional[InputMediaPhoto] = None
        self.empty_message = "⭕️ у вас пока нет избранных товаров."
        self.empty_image: str = "favorite"
        self.action = FavoriteAction
        self.call_data = FavoriteCBD
        self.kb_factory = FavoritePaginationBtn
        self.deserializer = DeserializedHandler()

    async def _get_favorite_list(self) -> List[History]:
        """Получает список истории и сохраняет его в self.array."""
        if self.array is None:
            self.array = await orm_get_favorite_list(self.user_id)
        return self.array

    async def _get_len(self) -> int:
        """Возвращает длину списка избранных товаров и сохраняет её в self.len."""
        if self.len is None:
            self.len = len(await self._get_favorite_list())
        return self.len

    async def _get_item(self) -> Favorite:
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
            current_item,
            str(self.page),
            await self._get_len()
        )

    async def get_media(self) -> InputMediaPhoto:
        """Возвращает медиа (фото с подписью) для текущего элемента избранных товаров."""
        if self.photo is None:
            if await self._get_len() > 0:
                try:
                    current_item = await self._get_item()
                    self.photo = InputMediaPhoto(
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

    async def get_keyboard(self) -> InlineKeyboardMarkup:
        """Возвращает клавиатуру для пагинации."""
        current_item = await self._get_item()
        if await self._get_len() >= 1:
            kb = self.kb_factory(
                item_id=str(current_item.uid),
                action=self.action,
                call_data=self.call_data
            )
            if await self._get_len() > 1:
                kb.create_pagination_buttons(
                    page=self.page,
                    navigate=self.navigate,
                    len_data=await self._get_len()
                )
            kb.add_buttons([
                kb.delete_btn(),
                kb.btn_text("menu")
            ]).add_markup(2)
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
        self.deserializer = DeserializedHandler()

    async def _is_favorite(self) -> bool:
        item_is_favorite = await orm_get_favorite(self.data.item_id)
        if item_is_favorite:
            raise IntegrityError("⚠️ уже добавлено в избранное")
        return bool(item_is_favorite)

    # if item:
    #    raise IntegrityError("⚠️ уже добавлено в избранное")

    async def _request_data(self):
        params = dict(
            url=config.URL_API_ITEM_DETAIL,
            itemId=self.data.item_id
        )
        return await request_api(params)

    async def _get_item_data(self):
        await self._is_favorite()
        if self.response is None:
            self.response = await self._request_data()
        if self.item is None:
            self.item = await deserializer.item_for_db(self.response, self.user_id)
            await orm_get_or_create_favorite(self.item)
        return self.item

    async def get_item(self):
        return self.item

    async def keyboard(self):
        kb = ItemPaginationBtn(
            key=self.data.key,
            api_page=self.data.api_page,
            paginator_len=int(self.data.last),
            item_id=self.data.item_id
        )
        if self.action == FavoriteAction.detail:
            kb.add_buttons([
                kb.detail('back', self.page, DetailAction.go_view),
                kb.btn_text('price')
            ]).add_markups([1, 2, 3])
        if self.action == FavoriteAction.list:
            data_web = ("url", await get_web_link(self.data.item_id))
            await kb.create_paginate_buttons(self.page)
            kb.add_buttons([
                kb.detail('view', self.page, DetailAction.go_view),
                kb.btn_text('menu'),
                kb.btn_data('web', data_web),
            ]).add_markup(3)

        return kb.create_kb()

    async def message(self):
        item_data = await self._get_item_data()
        msg = "<b>{0:.50}</b>\n".format(item_data["title"])
        msg += "💰\t\tцена:\t\t<b>{0}</b> RUB\n".format(item_data["price"])
        msg += "👀\t\tзаказы:\t\t<b>{0}</b>\n".format(item_data["reviews"])
        msg += "🌐\t\t{0}\n\n".format(item_data["url"])
        msg += "<b>{0}</b> из {1} стр. {2}\t".format(self.page, self.data.last, self.api_page)
        is_favorite = await orm_get_favorite(self.data.item_id)
        if is_favorite:
            msg += "👍\tв избранном"
        return InputMediaPhoto(media=item_data["image"], caption=msg)


class FavoriteDeleteManager:
    def __init__(self, callback_data, user_id):
        self.user_id = user_id
        self.page = int(callback_data.page)
        self.item_id = callback_data.item_id
        self.current_page = 1
        self.array: Optional[list] = None
        self.len: Optional[int] = None
        self.item: Optional[dict] = None
        self.photo: Optional[InputMediaPhoto] = None
        self.empty_message = "⭕️ у вас пока нет избранных товаров."
        self.empty_image: str = "favorite"
        self.action = FavoriteAction
        self.call_data = FavoriteDeleteCBD
        self.kb_factory = FavoritePaginationBtn
        self.deserializer = DeserializedHandler()

    async def _get_favorite_list(self) -> List[History]:
        """Получает список истории и сохраняет его в self.array."""
        await orm_delete_favorite(self.item_id)
        if self.array is None:
            self.array = await orm_get_favorite_list(self.user_id)
        return self.array

    async def _get_len(self) -> int:
        """Возвращает длину списка избранных товаров и сохраняет её в self.len."""
        if self.len is None:
            self.len = len(await self._get_favorite_list())
        return self.len

    async def _get_item(self) -> Favorite:
        """Возвращает элемент избранных товаров для текущей страницы."""
        try:
            if await self._get_len() > 0:
                # if self.item is None and await self._get_len() > 0:
                paginator = Paginator(await self._get_favorite_list(), page=self.page)
                self.item = paginator.get_page()[0]
            return self.item
        except IndexError:
            paginator = Paginator(await self._get_favorite_list(), page=self.page - 1)
            self.item = paginator.get_page()[0]
        return self.item

    async def get_msg(self) -> str:
        """Возвращает сообщение для текущего элемента избранных товаров."""
        current_item = await self._get_item()
        print('get msg page =', self.page)
        return await self.deserializer.favorite(
            current_item,
            await self._get_page(),
            await self._get_len()
        )

    async def _get_page(self):
        return self.page

    async def get_media(self) -> InputMediaPhoto:
        """Возвращает медиа (фото с подписью) для текущего элемента избранных товаров."""
        # if self.photo is None:
        if await self._get_len() > 0:
            try:
                current_item = await self._get_item()
                self.photo = InputMediaPhoto(
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

    async def get_keyboard(self) -> InlineKeyboardMarkup:
        """Возвращает клавиатуру для пагинации."""
        current_item = await self._get_item()
        print(f"🟥 page{self.page}")
        try:
            print(f"🟥 price before{current_item.price}")
        except AttributeError:
            pass
        paginator_length = await self._get_len()

        if paginator_length >= 1:
            is_first = self.array[0].uid == current_item.uid
            kb = self.kb_factory(
                item_id=str(current_item.uid),
                action=self.action,
                call_data=self.call_data
            )
            if paginator_length == 1:
                msg = "❤️1 page = 1 items"
            else:
                if paginator_length == 2:
                    if self.page == 1:
                        # Если удаляем первый товар из двух - переходим на следующую страницу
                        if is_first:  # Предполагаем, что есть такой атрибут
                            self.page += 1
                        kb.add_button(kb.pg(self.page).next_btn())
                        msg = '🧡first page 2 items'
                    elif self.page == paginator_length:
                        # Если удаляем последний товар - переходим на предыдущую страницу
                        if not is_first:
                            self.page -= 1
                        kb.add_button(kb.pg(self.page).prev_btn())
                        msg = '💛last page 2 items'
                    elif self.page > paginator_length:
                        self.page = paginator_length
                        self.current_page = self.page
                        kb.add_button(kb.pg(self.page).prev_btn())
                        msg = '🤎 last page 2 items'
                elif paginator_length > 2:
                    if self.page == 1:
                        # Если удаляем первый товар - переходим вперед
                        if is_first:
                            self.page += 1
                        kb.add_button(kb.pg(self.page).next_btn())
                        msg = '💚first page many items'
                    elif 1 < self.page < paginator_length:
                        # В середине списка - переходим назад, если не первый товар на странице
                        if not is_first:
                            self.page -= 1
                        kb.add_buttons([
                            kb.pg(self.page).prev_btn(),
                            kb.pg(self.page).next_btn()
                        ])
                        msg = '💙middle page many items'
                    elif self.page == paginator_length:
                        # На последней странице - переходим назад, если не первый товар
                        if not is_first:
                            self.page -= 1
                        kb.add_button(kb.pg(self.page).prev_btn())
                        msg = '🤍 last page many items == '
                    elif self.page > paginator_length:
                        self.page -= 1
                        self.current_page = self.page
                        kb.add_button(kb.pg(self.page).prev_btn())
                        msg = '💜 last page many items'
            current_item = await self._get_item()
            if current_item:
                kb.add_button(kb.delete_btn(current_item.product_id))
            kb.add_button({"🏠 меню": "menu"}).add_markups([2, 2])

            return kb.create_kb()

        else:
            return await kbm.back()
