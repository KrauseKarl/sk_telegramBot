from typing import Optional

from aiogram.types import InputMediaPhoto

from api_aliexpress.deserializers import DeserializedHandler
from api_aliexpress.request import *
from api_redis.handlers import *
from api_telegram import DetailAction
from api_telegram import ItemPaginationBtn
from database import orm, PaginatorHandler
from database.exceptions import *
from database.pydantic import *
from utils.cache_key import get_query_from_db, check_current_state, CacheKeyManager

redis_handler = RedisHandler()


async def get_web_link(item_id: str):
    return "https://www.aliexpress.com/item/{0}.html".format(item_id)


class ItemManager:
    def __init__(self, state, callback_data, callback):
        self.state = state
        self.callback_data = callback_data
        self.callback = callback
        self.user_id = callback.from_user.id

        self.params: Optional[dict] = None
        self.paginator_params: Optional[dict] = None
        self.array: Optional[list] = None
        self.page: Optional[int] = None
        self.cache_key: Optional[str] = None
        self.extra = 'list'

        self.cache_key_handler = CacheKeyManager()
        self.redis_handler = RedisHandler()
        self.deserializer = DeserializedHandler()

    async def message(self):
        if self.paginator_params is None:
            self.paginator_params = await self.get_paginate_params()
        msg, img, item_id = await self.deserializer.item_list(
            self.paginator_params
        )
        is_favorite = await orm.favorite.get_item(item_id)
        if is_favorite:
            msg += "👍\tв избранном"
        return InputMediaPhoto(media=img, caption=msg)

    async def keyboard(self):
        if self.paginator_params is None:
            self.paginator_params = await self.get_paginate_params()
        key = self.paginator_params.get("key")
        api_page = self.paginator_params.get("api_page")
        page = self.paginator_params.get("page")
        item_id = self.paginator_params.get("item").get('itemId')
        len_data = self.paginator_params.get("total_pages")

        kb = ItemPaginationBtn(
            key=key,
            api_page=int(api_page),
            paginator_len=len_data,
            item_id=item_id
        )
        await kb.create_paginate_buttons(page)
        data_web = ("url", await get_web_link(item_id))
        kb.add_buttons([
            kb.detail('detail', page, DetailAction.go_view),
            kb.btn_text("menu"),
            kb.btn_data("web", data_web),
        ]).add_markup(3)

        is_favorite = await orm.favorite.get_item(item_id)
        if is_favorite is None:
            kb.add_button(kb.favorite(page)).update_markup(4)
        return kb.create_kb()

    async def _generate_key(self, api_page):
        # print('generate_key ⚠️ api_page = ', self.callback_data.api_page, '|', api_page)
        return await CacheKeyManager.generate_key(
            key=self.callback_data.key,
            api_page=api_page,
            extra=self.extra
        )

    async def items_array(self):
        """
        """
        if self.params is None:
            self.params = await self.get_params_from_state()
        self.cache_key = await self._generate_key(self.callback_data.api_page)
        self.array = await self.redis_handler.get_from_cache(self.cache_key)
        self.page = int(self.callback_data.page) if int(self.callback_data.page) else 1

        if self.array is None:
            self.page = int(self.callback_data.page)
            self.params['page'] = self.callback_data.api_page
            self.array = await self._get_data_by_request_to_api()
            await self.redis_handler.set_in_cache(self.cache_key, self.array)
            await self._update_query_in_db(self.callback_data.key)

        if int(self.callback_data.api_page) == 0 or self.page > len(self.array):
            self.page = 1
            api_page = self.callback_data.api_page \
                if self.callback_data.api_page \
                else self.params['page']
            self.params['page'] = str(int(api_page) + 1)
            self.array = await self._get_data_by_request_to_api()
            self.cache_key = await self._generate_key(self.params['page'])
            await self.redis_handler.set_in_cache(self.cache_key, self.array)
            await self._update_query_in_db(self.callback_data.key)
        else:
            self.page = int(self.callback_data.page)
            if int(self.params['page']) > int(self.callback_data.api_page):
                self.params['page'] = self.callback_data.api_page
                self.cache_key = await self._generate_key(self.params['page'])
                self.array = await self.redis_handler.get_from_cache(self.cache_key)
                if self.array is None:
                    self.array = await self._get_data_by_request_to_api()
                    await self.redis_handler.set_in_cache(self.cache_key, self.array)
                    await self._update_query_in_db(self.callback_data.key)

        return self.array

    async def get_params_from_state(self):

        # self.params state | DB
        # self.callback_data get | None

        if self.callback_data is None:
            self.callback_data = await self._create_callback_data()
        is_state = await check_current_state(self.state, self.callback)
        if is_state:

            await self.state.update_data(sort=self.callback.data)
            state_data = await self.state.get_data()
            params = dict(
                q=state_data.get('product'),
                page=self.callback_data.api_page if self.callback_data else 1,
                sort=state_data.get('sort'),
                startPrice=state_data.get('price_min'),
                endPrice=state_data.get('price_max'),
                user_id=self.callback.from_user.id,
                command='search'
            )
            await self.state.set_state(state=None)
        else:
            params = await get_query_from_db(self.callback_data.key)
        params['url'] = config.URL_API_ITEM_LIST
        return params

    async def get_paginate_params(self):
        if self.array is None:
            self.array = await self.items_array()
        paginator = PaginatorHandler(self.array, self.page)
        itm_data = await paginator.get_item
        total_pages = await paginator.get_paginator_len
        return {
            "key": self.callback_data.key,
            "api_page": int(self.params['page']),
            "page": self.page,
            "item": itm_data['item'],
            "total_pages": total_pages
        }

    async def _create_callback_data(self) -> ItemCBD:
        new_key, created = await self.cache_key_handler.get_or_create_key(
            self.callback_data
        )
        self.callback_data = ItemCBD(
            key=new_key if created else self.callback_data.key,
            api_page=1,
            page=1
        )
        if created:
            await self._save_query_in_db(new_key, 1)
        return self.callback_data

    async def _save_query_in_db(self, key: str, page: int):
        data = dict(self.callback_data)
        data['page'] = str(page)
        query_str = json.dumps(data, ensure_ascii=False)
        save_query_dict = CacheDataModel(
            user=int(self.user_id),
            key=str(key),
            query=str(query_str)
        ).model_dump()
        await orm.query.save_in_db(save_query_dict)

    async def _update_query_in_db(self, key: str):
        query_str = json.dumps(self.params, ensure_ascii=False)
        update_query_dict = CacheDataUpdateModel(query=str(query_str)).model_dump()
        await orm.query.update_in_db(update_query_dict.get('query'), key)

    async def _get_data_by_request_to_api(self):
        if self.params is None:
            self.params = await self.get_params_from_state()
        response = await request_api(self.params)
        try:
            if self.params.get('q'):
                return response["result"]["resultList"]
            else:
                return response
        except KeyError:
            if "message" in response:
                raise FreeAPIExceededError(
                    message="⚠️HTTP error\n{0}".format(
                        response.get('message')
                    )
                )
