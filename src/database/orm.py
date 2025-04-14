import typing as t

from peewee import Model

from src.database import models as m
from src.database import pydantic


class UserORM:
    """Класс для работы с пользователями в базе данных (ORM слой)."""

    def __init__(self, model: t.Type[m.User]):
        self.model = model

    async def get_or_create(self, user: m.User) -> str:
        """
        Создает нового пользователя или возвращает существующего.

        Ищет пользователя по ID. Если пользователь не найден,
        создает новую запись в базе данных.

        :param user - Объект пользователя, который должен содержать.
        :return str - Приветственное сообщение.
        """
        user, created = self.model.get_or_create(
            user_id=user.id,
            user_name=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
        )
        if created:
            return "🟨 🤚 Добро пожаловать"
        return "🤝 Рады снова видеть вас"


class CacheORM:
    """Класс для работы с запросами в базе данных (ORM слой)."""

    def __init__(self, model: t.Type[Model]):
        self.model = model

    async def save_in_db(self, data: dict):
        """
        Сохраняет данные запроса в БД.
        :param data: Словарь с данными запроса.
        :return: None
        """
        self.model().create(**data).save()

    async def update_in_db(self, data: t.Dict[str, t.Any], key: str) -> None:
        """
        Обновляет данные запроса в БД.
        :param data: Словарь с данными запроса.
        :param key: ключ для поиска кэш-данных в БД.
        :return: None
        """
        self.model.update(query=data).where(m.CacheData.key == key).execute()

    async def get_from_db(self, key: str) -> t.Optional[m.CacheData]:
        """
        Берет данные запроса в БД.
        :param key: ключ для поиска кэш-данных в БД.
        :return: кэшированные данные
        """
        return self.model.select().where(m.CacheData.key == key).get_or_none()


class FavoriteORM:
    """Класс для работы с избранными товарами в базе данных (ORM слой)."""

    def __init__(self, model: t.Type[m.Favorite]):
        self.model = model

    async def create_item(self, data: t.Dict[str, t.Any]) -> None:
        """Создайте новый избранный товар"""
        self.model.create(**data).save()

    async def get_list(self, user_id: int) -> t.List[Model]:
        """Получите все избранные товары пользователя, упорядоченные по дате"""
        return (
            self.model.select()
            .where(self.model.user == user_id)
            .order_by(self.model.date.desc())
        )

    async def get_or_create(self, data: t.Dict[str, t.Any]) -> t.Tuple[Model, bool]:
        """Получите или создайте избранный товар"""
        return self.model.get_or_create(
            product_id=data.get("product_id"),
            title=data.get("title"),
            price=data.get("price"),
            reviews=data.get("reviews"),
            stars=data.get("stars"),
            url=data.get("url"),
            image=data.get("image"),
            user=data.get("user"),
        )

    async def delete(self, item_id: str) -> int:
        """Удалите избранную запись по ID"""
        return self.model.delete().where(self.model.uid == item_id).execute()

    async def get_item(self, product_id: str) -> t.Optional[Model]:
        """Получите избранную запись по ID продукта"""
        return (
            self.model.select().where(self.model.product_id == product_id).get_or_none()
        )


class MonitoringORM:
    """Класс для работы с отслеживаемыми товарами в базе данных (ORM слой)."""

    def __init__(self, model: t.Type[m.ItemSearch], sub_model: t.Type[m.DataEntry]):
        self.model = model
        self.sub_model = sub_model

    async def get_list(self, user_id: int):
        """
        Получить все элементы мониторинга для конкретного пользователя,
        упорядоченные по дате в порядке убывания
        """
        return (
            self.model.select()
            .where(self.model.user == user_id)
            .order_by(self.model.date.desc())
        )

    async def get_item(self, product_id: str):
        """Получить единый элемент мониторинга по product_id"""
        return (
            self.model.select().where(self.model.product_id == product_id).get_or_none()
        )

    async def get_item_by_id(self, uid: str):
        """Получить единый элемент мониторинга по ID"""
        return self.model.select().where(self.model.uid == uid).get_or_none()

    async def get_all_items(
        self,
    ):
        """Получение всех элементов мониторинга"""
        return [itm for itm in self.model.select()]

    async def create_item(self, data: dict):
        self.model.create(
            product_id=data.get("product_id"),
            title=data.get("title"),
            price=data.get("price"),
            url=data.get("url"),
            image=data.get("image"),
            user=data.get("user"),
            target=data.get("target"),
        ).save()

    async def delete_item(self, item_id: int):
        """Удаление элемента мониторинга по его ID"""
        self.model.delete().where(self.model.uid == item_id).execute()

    async def get_monitor_data(self, item_search):
        """Получение данных по отслеживаемому товару."""
        return (
            self.sub_model.select()
            .where(self.sub_model.item_search == item_search)
            .order_by(self.sub_model.date)
        )

    async def update(self, item_search_id, target_prise):
        return (
            self.model.update(target=target_prise)
            .where(self.model.uid == item_search_id)
            .execute()
        )


class HistoryORM:
    """Класс для работы с историей просмотра в базе данных (ORM слой)."""

    def __init__(self, model: t.Type[m.History]):
        self.model = model

    async def create(self, data: t.Dict[str, t.Any]) -> None:
        """Создает или обновляет запись."""
        is_exist = await self.get_item(str(data.get("product_id")))
        if not is_exist:
            pydantic.HistoryModel(
                user=data.get("user"),
                product_id=str(data.get("product_id")),
                title=data.get("title"),
                price=float(data.get("price")),
                reviews=int(data.get("reviews")),
                stars=float(data.get("stars")),
                url=data.get("url"),
                image=data.get("image"),
            ).model_dump()
            self.model().create(**data).save()

    async def get_item(self, product_id: str) -> t.Optional[m.History]:
        """Получает запись по product_id."""
        return (
            self.model.select().where(self.model.product_id == product_id).get_or_none()
        )

    async def get_item_by_id(self, item_id):
        """Получает запись по ID."""
        return self.model.select().where(self.model.uid == item_id).get_or_none()

    async def get_list(self, user_id: int) -> t.List[m.History]:
        """
        Получите все записи для пользователя,
        упорядоченные по дате (сначала самая новая).
        """
        return (
            self.model.select()
            .where(self.model.user == user_id)
            .order_by(self.model.date.desc())
        )


users = UserORM(m.User)
query = CacheORM(m.CacheData)
history = HistoryORM(m.History)
favorite = FavoriteORM(m.Favorite)
monitoring = MonitoringORM(m.ItemSearch, m.DataEntry)
