from aiogram.types import InputMediaPhoto
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from aiogram import Bot, types
from datetime import datetime

from pydantic import ValidationError

from api_aliexpress.deserializers import deserialize_item_detail
from api_telegram.crud.items import *
from api_telegram.keyboard.builders import kbm
from api_telegram.keyboards import BasePaginationBtn, ItemSearchPaginationBtn
from api_telegram.paginations import paginate_monitor_kb
from database.models import *
from utils.media import get_input_media_hero_image

scheduler = AsyncIOScheduler()


# Функция для удаления задачи
def remove_job(item_search_id: int):
    job_id = f"fetch_data_{item_search_id}"  # Уникальный ID задачи
    if scheduler.get_job(job_id):  # Проверяем, существует ли задача
        scheduler.remove_job(job_id)  # Удаляем задачу
        print(f"Задача {job_id} удалена из планировщика.")
    else:
        print(f"Задача {job_id} не найдена.")


async def create_item_search(item_search_id: int | str, user_id: int):
    response = await get_data_by_request_to_api(
        params={
            "itemId": item_search_id,
            "url": config.URL_API_ITEM_DETAIL
        }
    )

    item = await deserialize_item_detail(response, user_id)
    item_search = ItemSearch.select().where(ItemSearch.product_id == item_search_id).get_or_none()
    if item_search:
        raise CustomError('Товар уже отслеживается')
    await orm_create_item_search(item)


# Функция для запроса данных и сохранения в базу данных
async def fetch_and_save_data(item_search_id: int | str):
    # response = requests.get(Config.API_URL)
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
def sync_scheduler_with_db():
    """
    Синхронизирует задачи в планировщике с записями ItemSearch в базе данных.
    """
    existing_item_search_ids = [item.id for item in ItemSearch.select()]
    jobs_to_remove = []

    # Проверяем задачи в планировщике
    for job in scheduler.get_jobs():
        job_item_search_id = int(job.id.split("_")[-1])  # Извлекаем ID из job.id
        if job_item_search_id not in existing_item_search_ids:
            jobs_to_remove.append(job.id)  # Задача для несуществующего ItemSearch

    # Удаляем задачи для несуществующих ItemSearch
    for job_id in jobs_to_remove:
        scheduler.remove_job(job_id)
        print(f"Задача {job_id} удалена из планировщика.")

    # Добавляем задачи для новых ItemSearch
    for item_search in ItemSearch.select():
        job_id = f"fetch_data_{item_search.uid}"
        if not scheduler.get_job(job_id):  # Если задача отсутствует
            scheduler.add_job(
                fetch_and_save_data,
                CronTrigger(hour=config.SCHEDULE_HOUR, minute=config.SCHEDULE_MIN),  # Запуск каждый день в 9:00
                args=[item_search.uid],  # Передаем ID ItemSearch
                id=job_id,  # Уникальный ID задачи
            )
            print(f'время {config.SCHEDULE_HOUR}:{config.SCHEDULE_MIN}')
            print(f"Задача {job_id} добавлена в планировщик.")


# Настройка планировщика
def setup_scheduler(bot: Bot):
    # Синхронизация при запуске
    sync_scheduler_with_db()

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
        self.array: Optional[list] = None
        self.len: Optional[int] = None
        self.item: Optional[dict] = None
        self.photo: Optional[InputMediaPhoto] = None
        self.empty_message = "⭕️ у вас пока нет отслеживаемых товаров"
        self.action = MonitorAction
        self.call_data = MonitorCBD
        self.kb_factory = ItemSearchPaginationBtn

    async def _get_monitor_list(self) -> List[History]:
        """Получает список истории и сохраняет его в self.array."""
        if self.array is None:
            self.array = await orm_get_monitoring_list(self.user_id)
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
        return await monitor_info(current_item, str(self.page), await self._get_len())

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
                        "favorite",
                        await self.get_msg()
                    )
            else:
                self.photo = await get_input_media_hero_image(
                    "favorite",
                    self.empty_message
                )
        return self.photo

    async def get_photo(self) -> Optional[str]:
        """Возвращает фото текущего элемента истории."""
        item = await self._get_item()
        return item.image if item else None

    async def get_keyboard(self):
        """Возвращает клавиатуру для пагинации."""
        if await self._get_len() >= 1:
            current_item = await self._get_item()
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

async def get_searched_items_list(query, data):
    data_list = await orm_get_monitoring_list(query.from_user.id)
    if len(data_list) > 0:
        paginator = Paginator(data_list, page=data.page)
        monitor_item = paginator.get_page()[0]
        img = monitor_item.image
        msg = await monitor_info(monitor_item, data.page, paginator.pages)
        # kb = await paginate_searched_items_list_kb(
        kb = await paginate_monitor_kb(
            page=int(data.page),
            item_id=monitor_item.product_id,
            navigate=data.navigate,
            len_data=paginator.len
        )
    else:
        msg = "⭕️ у вас пока нет отслеживаемых товаров"
        img = None
        kb = BasePaginationBtn()
        kb.add_button(kb.btn_text('menu')).add_markup(1)
    try:
        # img = types.FSInputFile(path=os.path.join(config.IMAGE_PATH, img))
        photo = types.InputMediaPhoto(media=img, caption=msg)
    except (ValidationError, TypeError):
        photo = await get_input_media_hero_image("favorite", msg)
    return msg, photo, kb
