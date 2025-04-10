import locale

from aiogram import types as t
from matplotlib import pyplot as plt

from api_telegram import MonitorAction, MonitorCBD, BasePaginationBtn
from database import orm, ItemSearch


class GraphManager:
    def __init__(self, callback_data, user_id):
        self.callback_data = callback_data
        self.item_id = callback_data.item_id
        self.user_id = user_id
        self.item_search = None
        self.entries = None
        self.values = None
        self.timestamps = None
        self.max_time_value = None
        self.max_value = None
        self.min_time_value = None
        self.min_value = None
        self.photo = None
        self.message = None
        self.kb_factory = BasePaginationBtn
        self.call_data = MonitorCBD

    async def _get_item_search(self) -> ItemSearch:
        """Получает поисковый запрос по ID."""
        if self.item_search is None:
            self.item_search = await orm.monitoring.get_item_by_id(self.item_id)
            if self.item_search is None:
                raise ValueError("Неверный ID поискового запроса.")
        return self.item_search

    async def _get_monitor_data(self) -> list:
        """Получает данные мониторинга для поискового запроса."""
        if self.entries is None:
            item_search = await self._get_item_search()
            self.entries = await orm.monitoring.get_monitor_data(item_search)
            if not self.entries:
                raise ValueError("Данные отсутствуют.")
        return self.entries

    def _setup_locale(self):
        """Устанавливает локаль для корректного отображения дат."""
        try:
            locale.setlocale(locale.LC_ALL, 'Russian')
        except locale.Error:
            try:
                locale.setlocale(locale.LC_ALL, 'ru_RU.UTF-8')
            except locale.Error:
                locale.setlocale(locale.LC_ALL, 'C.UTF-8')

    def _prepare_graph_data(self):
        """Подготавливает данные для графика."""
        if self.values is None or self.timestamps is None:
            self.values = [entry.value for entry in self.entries]
            self.timestamps = [entry.date.strftime('%b %d') for entry in self.entries]

    def _find_extremes(self):
        """Находит максимальные и минимальные значения на графике."""
        if None in (self.max_time_value, self.max_value, self.min_time_value, self.min_value):
            self.max_value = max(self.values)
            self.min_value = min(self.values)

            # Находим последние вхождения максимального и минимального значений
            max_dict = {x: y for x, y in zip(self.timestamps, self.values) if y == self.max_value}
            min_dict = {x: y for x, y in zip(self.timestamps, self.values) if y == self.min_value}

            self.max_time_value = sorted(max_dict.items())[-1][0]
            self.min_time_value = sorted(min_dict.items())[-1][0]

    def _create_graph(self):
        """Создает график и сохраняет его в файл."""
        plt.style.use('dark_background')
        plt.figure(figsize=(20, 9), dpi=300)
        plt.ylim(
            min(self.values) - min(self.values) * 0.25,
            max(self.values) + min(self.values) * 0.25
        )
        plt.plot(
            self.timestamps,
            self.values,
            color='grey',
            marker="o",
            markersize=20,
            linewidth=5
        )

        # Добавляем аннотации для экстремумов и последнего значения
        for x, y in zip(self.timestamps, self.values):
            if x == self.max_time_value:
                plt.text(x, y,
                         f'{y}',
                         fontsize=20,
                         ha='center',
                         va='bottom',
                         color='white',
                         bbox=dict(facecolor='red', alpha=0.8))
            if x == self.min_time_value:
                plt.text(x, y,
                         f'{y}',
                         fontsize=20,
                         ha='center',
                         va='bottom',
                         color='white',
                         bbox=dict(facecolor='green', alpha=0.8))
            if self.values[-1] == y:
                plt.text(x, y, f'{y}', fontsize=20, ha='center', va='bottom', color='white',
                         bbox=dict(facecolor='orange', alpha=0.8))

        # Добавляем информацию о максимуме и минимуме
        plt.text(0.99, 0.99,
                 f'Максимум: {self.max_value}',
                 horizontalalignment='right',
                 verticalalignment='top',
                 transform=plt.gca().transAxes,
                 fontsize=25,
                 color='white',
                 bbox=dict(facecolor='red', alpha=0.8))
        plt.text(0.99, 0.90,
                 f'Минимум: {self.min_value}',
                 horizontalalignment='right',
                 verticalalignment='top',
                 transform=plt.gca().transAxes,
                 fontsize=25,
                 color='white',
                 bbox=dict(facecolor='green', alpha=0.8))

        # Настраиваем заголовок и оси
        item_search = self.item_search
        plt.title(
            "График изменения цены для '{0:.25}'".format(item_search.title),
            fontdict=dict(color='white', fontsize=22)
        )
        plt.xlabel("Период", fontdict=dict(color='white', fontsize=25))
        plt.ylabel("Цена", fontdict=dict(color='white', fontsize=25))
        plt.grid(axis='y', visible=True, linestyle='-', alpha=0.5)
        plt.grid(axis='x', visible=True, linestyle='-', alpha=0.3)
        plt.xticks(self.timestamps)
        plt.savefig("graph.png")

    async def get_media(self) -> t.InputMediaPhoto:
        """Возвращает медиа с графиком и подписью."""
        if self.photo is None:
            await self._get_monitor_data()
            self._setup_locale()
            self._prepare_graph_data()
            self._find_extremes()
            self._create_graph()

            msg = (f"\r\n📈 max цена = {self.max_value}\t({self.max_time_value})\r\n"
                   f"📉 min цена = {self.min_value}\t({self.min_time_value})\r\n"
                   f"📅 текущая цена = {self.values[-1]}\t({self.timestamps[-1]})\r\n")

            self.photo = t.InputMediaPhoto(
                media=t.FSInputFile("graph.png"),
                caption=msg
            )
        return self.photo

    async def get_keyboard(self):
        """Возвращает клавиатуру для графика."""
        kb = self.kb_factory()
        kb_data = self.call_data(
            action=MonitorAction.list,
            navigate=self.callback_data.navigate,
            monitor_id=self.callback_data.monitor_id,
            item_id=self.callback_data.item_id,
            page=self.callback_data.page
        ).pack()
        kb.add_button(kb.btn_data('back', kb_data)).add_markup(1)
        return kb.create_kb()
