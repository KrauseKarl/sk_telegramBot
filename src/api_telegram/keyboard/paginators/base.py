import typing as t

from src.api_telegram import Navigation
from src.api_telegram.keyboard import factories


class PaginationBtn(factories.BasePaginationBtn):
    """Базовый класс для создания клавиатуру с пагинацией"""
    def __init__(self, action, call_data, item_id=None):
        super().__init__()
        self.page = 1
        self.item_id = item_id
        self.action = action
        self.navigate = Navigation
        self.call_data = call_data

    def pg(self, page):
        """Устанавливает значение страницы"""
        self.page = page
        return self

    def __add__(self, other: int) -> int:
        """Добавляет к текущей страницы определённое значение"""
        if other:
            return self.page + other
        return self.page

    def increase(self, obj: t.Optional[int]) -> t.Optional[int]:
        """Увеличивает значение на один шаг"""
        return int(obj) + 1 if obj else None

    def decrease(self, obj: t.Optional[int]) -> t.Optional[int]:
        """Уменьшает значение на один шаг"""
        return int(obj) - 1 if obj else None

    def _btn(self, num: int, navigate: str, action: str, *args, **kwargs):
        """Возвращает callback данные кнопки."""
        return self.call_data(
            action=action, navigate=navigate, page=self.__add__(num)
        ).pack()

    def next_btn(self, sub_page=None, *args, **kwargs):  # page + 1
        """Возвращает callback данные кнопки `next`."""
        return self.btn_data(
            name="next",
            data=self._btn(
                num=1,
                navigate=self.navigate.next,
                action=self.action.paginate,
                sub_page=None,
                *args,
                **kwargs,
            ),
        )

    def prev_btn(self, sub_page=None, *args, **kwargs):  # page - 1
        """Возвращает callback данные кнопки `previous`."""
        return self.btn_data(
            name="prev",
            data=self._btn(
                num=-1,
                navigate=self.navigate.prev,
                action=self.action.paginate,
                sub_page=None,
                *args,
                **kwargs,
            ),
        )

    def create_pagination_buttons(
            self, page, navigate, len_data, sub_page=None, *args, **kwargs
    ):
        """Создает клавиатуру для пагинации списка объектов."""
        if navigate == Navigation.first:
            self.add_button(
                self.pg(page).next_btn(sub_page=self.increase(sub_page), *args, **kwargs)
            )
        elif navigate == Navigation.next:
            self.add_button(
                self.pg(page).prev_btn(sub_page=self.decrease(sub_page), *args, **kwargs)
            )
            if page < len_data:
                self.add_button(
                    self.pg(page).next_btn(sub_page=self.increase(sub_page), *args, **kwargs)
                )
        elif navigate == Navigation.prev:
            if page > 1:
                self.add_button(
                    self.pg(page).prev_btn(sub_page=self.decrease(sub_page), *args, **kwargs)
                )
            self.add_button(
                self.pg(page).next_btn(sub_page=self.increase(sub_page), *args, **kwargs)
            )
        self.add_markup(2 if len(self.get_kb()) == 2 else 1)
        return self
