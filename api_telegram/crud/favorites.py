from aiogram.types import CallbackQuery
from pydantic import ValidationError

from api_aliexpress.deserializers import *
from api_aliexpress.request import *
from api_telegram.callback_data import *
from api_telegram.keyboard.builders import kbm
from api_telegram.keyboards import *
from api_telegram.paginations import *
from core import config
from utils.message_info import favorite_info


async def create_favorite_instance(call: CallbackQuery, data: FavoriteAddCBD):
    """

    :param data:
    :param call:
    :return:
    """

    item = await orm_get_favorite(data.item_id)
    print(f'🌳🌳🌳 favorite exist = {item}')
    if item:
        raise IntegrityError("⚠️ уже добавлено в избранное")
    #####################################################
    params = {
        "url": config.URL_API_ITEM_DETAIL,
        "itemId": data.item_id
    }
    response = await request_api(params)
    item_data = await deserialize_item_detail(response, call.from_user.id)
    ##########################################################
    item_data["product_id"] = data.item_id
    await orm_get_or_create_favorite(item_data)
    item_data["command"] = "item detail"
    kb = ItemPaginationBtn(
        key=data.key,
        api_page=data.api_page,
        paginator_len=int(data.last),
        item_id=data.item_id
    )
    if data.action == FavoriteAction.detail:
        kb.add_buttons([
            kb.detail('back', data.page, DetailAction.go_view),
            kb.btn_text('price')
        ]).add_markups([1, 2, 3])
    if data.action == FavoriteAction.list:
        kb.add_buttons([
            kb.btn_data('prev', data.prev),
            kb.btn_data('next', data.next),
            kb.btn_data('first', data.first),
            kb.btn_data('last', data.last),
            kb.detail('view', data.page, DetailAction.go_view),
            kb.btn_text('menu'),
            kb.btn_text('web'),
        ]).add_markups([2, 2, 3])

    return item_data, kb.create_kb()


async def delete_favorite_instance(item_id: str) -> bool:
    favorite_obj = await orm_get_favorite(item_id)
    # await delete_img_from_static(favorite_obj)
    try:
        await orm_delete_favorite(item_id)
        return True
    except Exception as error:
        print("delete error = ", error)
        return False


class FavoriteManager:
    def __init__(self, callback_data, user_id):
        self.user_id = user_id
        self.page = int(callback_data.page)
        self.navigate = callback_data.navigate
        self.array: Optional[list] = None
        self.len: Optional[int] = None
        self.item: Optional[dict] = None
        self.photo: Optional[InputMediaPhoto] = None
        self.empty_message = "⭕️ у вас пока нет избранных товаров."
        self.action = FavoriteAction
        self.call_data = FavoriteCBD
        self.kb_factory = FavoritePaginationBtn

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
        if self.item is None and await self._get_len() > 0:
            paginator = Paginator(await self._get_favorite_list(), page=self.page)
            self.item = paginator.get_page()[0]
        return self.item

    async def get_msg(self) -> str:
        """Возвращает сообщение для текущего элемента избранных товаров."""
        current_item = await self._get_item()
        return await favorite_info(current_item, str(self.page), await self._get_len())

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
                        "history",
                        await self.get_msg()
                    )
            else:
                self.photo = await get_input_media_hero_image(
                    "history",
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
            kb.create_pagination_buttons(
                page=self.page,
                navigate=self.navigate,
                len_data=int(await self._get_len())
            )
            kb.add_buttons([
                kb.delete_btn(),
                kb.btn_text("menu")
            ]).add_markup(2)
            return kb.create_kb()
        else:
            return await kbm.back()
