from api_telegram import Navigation
from api_telegram.keyboard import factories


class PaginationBtn(factories.BasePaginationBtn):
    def __init__(self, action, call_data, item_id=None):
        super().__init__()
        self.page = 1
        self.item_id = item_id
        self.action = action
        self.navigate = Navigation
        self.call_data = call_data

    def pg(self, page):
        self.page = page
        return self

    def __add__(self, other):
        if other:
            return self.page + other
        return self.page

    def increase(self, obj):
        if obj:
            return int(obj) + 1

    def decrease(self, obj):
        if obj:
            return int(obj) - 1

    def _btn(self, num, navigate, action, *args, **kwargs):
        return self.call_data(
            action=action,
            navigate=navigate,
            page=self.__add__(num)
        ).pack()

    def next_btn(self, num: int = 1, sub_page=None, *args, **kwargs):  # page + 1
        return self.btn_data(
            name='next',
            data=self._btn(
                num=num,
                navigate=self.navigate.next,
                action=self.action.paginate,
                sub_page=None,
                *args,
                **kwargs
            )
        )

    def prev_btn(self, num: int = -1, sub_page=None, *args, **kwargs):  # page - 1
        return self.btn_data(
            name='prev',
            data=self._btn(
                num=num,
                navigate=self.navigate.prev,
                action=self.action.paginate,
                sub_page=None,
                *args,
                **kwargs
            )
        )

    def create_pagination_buttons(self, page, navigate, len_data, sub_page=None, *args, **kwargs):
        if navigate == Navigation.first:
            self.add_button(
                self.pg(page).next_btn(1, self.increase(sub_page), *args, **kwargs)
            )
        elif navigate == Navigation.next:
            self.add_button(
                self.pg(page).prev_btn(-1, self.decrease(sub_page), *args, **kwargs)
            )
            if page < len_data:
                self.add_button(
                    self.pg(page).next_btn(1, self.increase(sub_page), *args, **kwargs)
                )
        elif navigate == Navigation.prev:
            if page > 1:
                self.add_button(
                    self.pg(page).prev_btn(-1, self.decrease(sub_page), *args, **kwargs)
                )
            self.add_button(
                self.pg(page).next_btn(1, self.increase(sub_page), *args, **kwargs)
            )
        self.add_markup(2 if len(self.get_kb()) == 2 else 1)
        return self

