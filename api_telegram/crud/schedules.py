import typing as t

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from api_aliexpress.deserializers import DeserializedHandler
from api_aliexpress.request import get_data_by_request_to_api
from api_redis import RedisHandler
from api_telegram import JobCBD, CacheKey, kbm, MonitorCBD, MonitorAction, Navigation
from api_telegram.keyboard.factories import BasePaginationBtn
from core import config
from database import ItemSearch, DataEntry
from database.exceptions import CustomError
from database import orm
from logger import logger as log
from utils.media import get_input_media_hero_image, get_fs_input_hero_image

scheduler = AsyncIOScheduler()


class DefineTargetManger:
    def __init__(self, state_data):
        self.product_id = state_data.get('product_id')
        self.target_prise = float(state_data.get('price'))
        self.callback = state_data.get('callback')

    async def define_target(self):
        item_search = await orm.monitoring.get_item_by_id(self.product_id)
        await orm.monitoring.update(item_search.uid, self.target_prise)

    async def message(self):
        return "Цена {0} установлена".format(self.target_prise)

    async def keyboard(self):
        navigate = self.callback.split(":")[2]
        page = self.callback.split(":")[-1]

        kb_data = MonitorCBD(
            action=MonitorAction.list,
            navigate=navigate,
            item_id=self.product_id,
            page=page
        ).pack()
        kb = BasePaginationBtn()
        kb.add_button(kb.btn_data('back', kb_data)).add_markup(1)
        return kb.create_kb()


class ScheduleManager:
    def __init__(self, bot: Bot):
        self.bot: Bot = bot
        self.scheduler = AsyncIOScheduler()
        self.deserializer = DeserializedHandler()
        self.redis_handler = RedisHandler()

    def remove_job(self, item_search_id):
        job_id = JobCBD(uid=item_search_id).pack()  # Уникальный ID задачи
        if self.scheduler.get_job(job_id):  # Проверяем, существует ли задача
            self.scheduler.remove_job(job_id)  # Удаляем задачу
            # todo add to logger
            print(f"Задача {job_id} удалена из планировщика.")
        else:
            # todo add to logger
            print(f"Задача {job_id} не найдена.")

    async def create_item_search(
            self,
            item_search_id: int,
            user_id: int,
            key: str,
            page: int,
            target_price: float = None):
        cache_key = CacheKey(
            key=key,
            api_page=page,
            extra='detail'
        ).pack()
        response = await self.redis_handler.get_data(cache_key)
        if response is None:
            response = await get_data_by_request_to_api(
                params={
                    "itemId": item_search_id,
                    "url": config.URL_API_ITEM_DETAIL
                }
            )
        item = await self.deserializer.item_for_db(response, user_id)
        item_search = await orm.monitoring.get_item(item_search_id)
        if item_search:
            raise CustomError('Товар уже отслеживается')

        # Добавляем target_price в создание товара
        item['target'] = target_price
        await orm.monitoring.create_item(item)

    async def fetch_and_save_data(self, item_search_id: int):
        """Функция для запроса данных и сохранения в базу данных"""
        item_search = await orm.monitoring.get_item_by_id(item_search_id)
        response = await get_data_by_request_to_api(
            params={
                "itemId": item_search.product_id,
                "url": config.URL_API_ITEM_DETAIL
            }
        )

        prices = response.get("result").get("item").get("sku").get("base")[0]
        current_price = float(prices.get("promotionPrice", prices.get('price')))
        item_search = ItemSearch.get_by_id(item_search_id)

        # Сохранение данных в базу
        DataEntry.create(
            value=current_price,
            item_search=item_search,  # Указываем связь с ItemSearch
        )
        # Проверка достижения целевой цены и отправка уведомления
        if item_search.target is not None and current_price <= item_search.target:
            # todo add in logger
            print(' Целевая цена достигнута')
            await self.send_price_alert(item_search_id, current_price)

    async def send_price_alert(self, item_search_id: int, current_price: float):
        """Отправляет уведомление пользователю о достижении целевой цены"""
        item_search = await orm.monitoring.get_item_by_id(item_search_id)
        if self.bot is None:
            # todo add in logger
            print("Bot is None, cannot send alert")
            return

        try:
            message = (
                "🚨 Целевая цена достигнута! 🚨\n\n"
                "Товар: {0:.50}\n"
                "💰 Текущая цена: {1} ₽\n"
                "👍 Ваша целевая цена: {2} ₽\n\n".format(
                    item_search.title,
                    current_price,
                    item_search.target
                )
            )
            kb = BasePaginationBtn()
            buttons = [
                kb.btn_data("list_searches",
                            MonitorCBD(
                                action=MonitorAction.list,
                                navigate=Navigation.first,
                                page=1
                            ).pack()
                            ),
                kb.btn_text('menu')
            ]
            kb.add_buttons(buttons)
            keyboard = kb.create_kb()
            log.info_log.info(kb.get_kb())
            try:
                await self.bot.edit_message_media(
                    chat_id=item_search.user_id,
                    media=await get_input_media_hero_image(
                        value='success',
                        msg=message
                    ),
                    reply_markup=keyboard
                )
            except TelegramBadRequest:
                await self.bot.send_photo(
                    chat_id=item_search.user_id,
                    caption=message,
                    photo=await get_fs_input_hero_image('success'),
                    reply_markup=keyboard
                )

            # Удаляем целевую цену после уведомления (опционально)
            await orm.monitoring.update(item_search.uid, None)

        except CustomError as error:
            print(f"Ошибка при отправке уведомления: {error}")
            # todo add to logger

    # Функция для синхронизации планировщика с базой данных
    async def sync_scheduler_with_db(self):
        """
        Синхронизирует задачи в планировщике с записями ItemSearch в базе данных.
        """
        existing_item_search_ids = await orm.monitoring.get_all_items()
        jobs_to_remove = []

        # Проверяем задачи в планировщике
        for job in self.scheduler.get_jobs():
            job_item_search_id = job.id
            if job_item_search_id not in existing_item_search_ids:
                jobs_to_remove.append(job.id)

                # Удаляем задачи для несуществующих ItemSearch
        for job_id in jobs_to_remove:
            self.scheduler.remove_job(job_id)
            # todo add to logger
            print(f"Задача {job_id} удалена из планировщика.")
        item_search_list = await orm.monitoring.get_all_items()

        # Добавляем задачи для новых ItemSearch
        # todo add to logger
        print(f'Всего задач {len(item_search_list)}')
        for item_search in item_search_list:
            job_id = JobCBD(uid=item_search.product_id).pack()
            if not self.scheduler.get_job(job_id):  # Если задача отсутствует
                self.scheduler.add_job(
                    self.fetch_and_save_data,
                    CronTrigger(hour=config.SCHEDULE_HOUR, minute=config.SCHEDULE_MIN),  # Запуск каждый день в 9:00
                    args=[item_search.uid],  # Передаем ID ItemSearch
                    # kwargs={'bot': self.bot},  # Передаем бота для отправки уведомлений
                    id=job_id,  # Уникальный ID задачи
                )
                print(f'время {config.SCHEDULE_HOUR}:{config.SCHEDULE_MIN}.\tЗадача {job_id} добавлена в планировщик.')

    # Настройка планировщика

    async def setup_scheduler(self):
        # Синхронизация при запуске
        await self.sync_scheduler_with_db()

        # Добавляем периодическую задачу для синхронизации (например, каждые 10 минут)
        self.scheduler.add_job(
            func=self.sync_scheduler_with_db,
            # IntervalTrigger(days=config.SCHEDULE_RANGE, ),
            # trigger=CronTrigger(day="*/1", hour=10, minute=30),
            trigger=IntervalTrigger(minutes=2),
            # args=[self.bot],
            id="sync_scheduler_with_db",
        )

        self.scheduler.start()
