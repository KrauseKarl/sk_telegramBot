import typing as t

from aiogram.client import bot
from aiogram.types import InputMediaPhoto, InlineKeyboardMarkup
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from aiogram import Bot
from pydantic import ValidationError

from api_aliexpress.deserializers import DeserializedHandler
from api_aliexpress.request import get_data_by_request_to_api
from api_redis import RedisHandler
from api_telegram import MonitorAction, MonitorCBD, JobCBD, CacheKey
from api_telegram import kbm, MonitorPaginationBtn
from core import config
from database import (
    orm_get_monitoring_item,
    orm_create_item_search,
    orm_get_monitoring_list,
    orm_get_all_monitor_items,
    orm_delete_monitor_item, Paginator
)
from database import ItemSearch, DataEntry, History, Favorite
from database.exceptions import CustomError
from utils.media import get_input_media_hero_image

scheduler = AsyncIOScheduler()
deserializer = DeserializedHandler()
redis_handler = RedisHandler()


# todo get togather in class
# Функция для удаления задачи
def remove_job(item_search_id: int):
    # job_id = f"fetch_data_{item_search_id}"  # Уникальный ID задачи
    job_id = JobCBD(uid=item_search_id).pack()  # Уникальный ID задачи
    print(f"{job_id= }")
    if scheduler.get_job(job_id):  # Проверяем, существует ли задача
        scheduler.remove_job(job_id)  # Удаляем задачу
        print(f"Задача {job_id} удалена из планировщика.")
    else:
        print(f"Задача {job_id} не найдена.")


async def create_item_search(item_search_id: int, user_id: int, key, page):
    cache_key = CacheKey(
        key=key,
        api_page=page,
        extra='detail'
    ).pack()
    response = await redis_handler.get_data(cache_key)
    if response is None:
        response = await get_data_by_request_to_api(
            params={
                "itemId": item_search_id,
                "url": config.URL_API_ITEM_DETAIL
            }
        )
    item = await deserializer.item_for_db(response, user_id)
    item_search = await orm_get_monitoring_item(item_search_id)
    if item_search:
        raise CustomError('Товар уже отслеживается')
    await orm_create_item_search(item)


# Функция для запроса данных и сохранения в базу данных
async def fetch_and_save_data(item_search_id: int):
    item_search = ItemSearch.get_by_id(item_search_id)
    response = await get_data_by_request_to_api(
        params={
            "itemId": item_search.product_id,
            "url": config.URL_API_ITEM_DETAIL
        }
    )

    prices = response.get("result").get("item").get("sku").get("base")[0]
    current_price = prices.get("promotionPrice", prices.get('price'))
    item_search = ItemSearch.get_by_id(item_search_id)
    # Сохранение данных в базу
    DataEntry.create(
        value=current_price,
        item_search=item_search,  # Указываем связь с ItemSearch
    )


# Функция для синхронизации планировщика с базой данных
async def sync_scheduler_with_db():
    """
    Синхронизирует задачи в планировщике с записями ItemSearch в базе данных.
    """
    existing_item_search_ids = await orm_get_all_monitor_items()
    jobs_to_remove = []

    # Проверяем задачи в планировщике
    for job in scheduler.get_jobs():
        # job_item_search_id = int(job.id.split("_")[-1])  # Извлекаем ID из job.id
        job_item_search_id = job.id  # Извлекаем ID из job.id
        print(f"{job_item_search_id= }")
        if job_item_search_id not in existing_item_search_ids:
            jobs_to_remove.append(job.id)  # Задача для несуществующего ItemSearch

    # Удаляем задачи для несуществующих ItemSearch
    for job_id in jobs_to_remove:
        scheduler.remove_job(job_id)
        print(f"Задача {job_id} удалена из планировщика.")
    item_search_list = ItemSearch.select()
    # Добавляем задачи для новых ItemSearch
    print(f'Всего задач {len(item_search_list)}')
    for item_search in item_search_list:
        # job_id = f"fetch_data_{item_search.uid}"
        job_id = JobCBD(uid=item_search.product_id).pack()
        if not scheduler.get_job(job_id):  # Если задача отсутствует
            scheduler.add_job(
                fetch_and_save_data,
                CronTrigger(hour=config.SCHEDULE_HOUR, minute=config.SCHEDULE_MIN),  # Запуск каждый день в 9:00
                args=[item_search.uid],  # Передаем ID ItemSearch
                id=job_id,  # Уникальный ID задачи
            )
            print(f'время {config.SCHEDULE_HOUR}:{config.SCHEDULE_MIN}.\tЗадача {job_id} добавлена в планировщик.')


# Настройка планировщика
async def setup_scheduler(bot: Bot):
    # Синхронизация при запуске
    await sync_scheduler_with_db()

    # Добавляем периодическую задачу для синхронизации (например, каждые 10 минут)
    scheduler.add_job(
        sync_scheduler_with_db,
        IntervalTrigger(minutes=10),  # Запуск каждые 10 минут
        id="sync_scheduler_with_db",  # Уникальный ID задачи
    )

    scheduler.start()


class MonitorManager:
    def __init__(self, callback_data, user_id):
        self.user_id = user_id
        self.page = int(callback_data.page)
        self.navigate = callback_data.navigate
        self.array: t.Optional[list] = None
        self.len: t.Optional[int] = None
        self.item: t.Optional[dict] = None
        self.photo: t.Optional[InputMediaPhoto] = None
        self.empty_message = "⭕️ у вас пока нет отслеживаемых товаров"
        self.empty_image = "favorite"
        self.action = MonitorAction
        self.call_data = MonitorCBD
        self.kb_factory = MonitorPaginationBtn
        self.deserializer = DeserializedHandler()

    async def _get_monitor_list(self) -> t.List[History]:
        """Получает список истории и сохраняет его в self.array."""
        if self.array is None:
            self.array = await orm_get_monitoring_list(self.user_id)
        # print('list', [i.uid for i in self.array])
        return self.array

    async def _get_len(self) -> int:
        """Возвращает длину списка истории и сохраняет её в self.len."""
        if self.len is None:
            self.len = len(await self._get_monitor_list())
        return self.len

    async def _get_item(self) -> History:
        """Возвращает элемент истории для текущей страницы."""
        if self.item is None and await self._get_len() > 0:
            paginator = Paginator(await self._get_monitor_list(), page=self.page)
            self.item = paginator.get_page()[0]
        return self.item

    async def get_msg(self) -> str:
        """Возвращает сообщение для текущего элемента истории."""
        current_item = await self._get_item()
        return await self.deserializer.monitor(
            current_item,
            self.page,
            await self._get_len()
        )

    async def get_media(self) -> InputMediaPhoto:
        """Возвращает медиа (фото с подписью) для текущего элемента истории."""
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
                call_data=self.call_data
            )
            if await self._get_len() > 1:
                kb.create_pagination_buttons(
                    page=self.page,
                    navigate=self.navigate,
                    len_data=int(await self._get_len())
                )
            kb.add_buttons(
                [
                    kb.graph_btn(self.navigate),
                    kb.delete_btn(self.navigate),
                    kb.btn_text("menu")
                ]
            ).add_markups([2, 1])
            return kb.create_kb()
        else:
            return await kbm.back()


class MonitorDeleteManager:
    def __init__(self, callback_data, user_id):
        self.user_id = user_id
        self.page = int(callback_data.page)
        self.item_id = callback_data.item_id
        self.navigate = callback_data.navigate
        self.array: t.Optional[list] = None
        self.len: t.Optional[int] = None
        self.item: t.Optional[dict] = None
        self.photo: t.Optional[InputMediaPhoto] = None
        self.empty_message: str = "⭕️ у вас пока нет отслеживаемых товаров"
        self.empty_image: str = "favorite"
        self.action = MonitorAction
        self.call_data = MonitorCBD
        self.kb_factory = MonitorPaginationBtn
        self.deserializer = DeserializedHandler()

    async def _get_list(self) -> t.List[History]:
        """Получает список истории и сохраняет его в self.array."""
        if self.array is None:
            self.array = await orm_get_monitoring_list(self.user_id)
        return self.array

    async def stop_monitoring_item(self):
        await orm_delete_monitor_item(self.item_id)

    async def _get_len(self) -> int:
        """Возвращает длину списка избранных товаров и сохраняет её в self.len."""
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
            current_item,
            self.page,
            await self._get_len()
        )

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

    async def get_photo(self) -> t.Optional[str]:
        """Возвращает фото текущего элемента истории."""
        current_item = await self._get_item()
        return current_item.image if current_item else None

    async def get_keyboard(self) -> InlineKeyboardMarkup:
        """Возвращает клавиатуру для пагинации."""

        paginator_length = await self._get_len()
        if paginator_length >= 1:
            current_item = await self._get_item()
            kb = self.kb_factory(
                item_id=str(current_item.uid),
                action=self.action,
                call_data=self.call_data
            )
            if paginator_length > 1:
                kb.create_pagination_buttons(
                    page=self.page,
                    navigate=self.navigate,
                    len_data=int(await self._get_len())
                )

            current_item = await self._get_item()
            if current_item:
                kb.add_buttons(
                    [
                        kb.graph_btn(self.navigate),
                        kb.delete_btn(self.navigate),
                        kb.btn_text("menu")
                    ]
                ).add_markups([2, 1])
            for k in kb.get_kb():
                if list(k.keys())[0] in ['⬅️ Пред.', 'След. ➡️']:
                    print('\t', k)
            return kb.create_kb()
        else:
            return await kbm.back()
