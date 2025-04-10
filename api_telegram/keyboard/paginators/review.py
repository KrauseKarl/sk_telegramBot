from typing import Optional

from api_telegram import Navigation, DetailCBD
from api_telegram.keyboard.paginators import PaginationBtn


class ReviewPaginationBtn(PaginationBtn):
    def __init__(self, action, call_data, item_id, key, api_page, paginator_len):
        super().__init__(action, call_data, item_id)
        self.page = 1
        self.first = 1
        self.key = key
        self.api_page = api_page
        self.len = paginator_len

    def next_btn(self, num, sub_page=None, *args, **kwargs):
        return self.btn_data(
            'next',
            self._btn(num, self.navigate.next, sub_page, *args, **kwargs)
        )

    def prev_btn(self, num, sub_page=None, *args, **kwargs):
        return self.btn_data(
            'prev',
            self._btn(num, self.navigate.prev, sub_page, *args, **kwargs)
        )

    def _btn(self, num: int, navigate: str, sub_page: Optional[int] = None, *args, **kwargs):  # page, sub_page
        return self.call_data(
            action=self.action.paginate,
            item_id=self.item_id,
            key=self.key,
            api_page=self.api_page,
            page=self.page,
            next=self.page + 1,
            prev=self.page - 1,
            first=self.first,
            last=self.len,
            navigate=navigate,
            sub_page=sub_page,
        ).pack()

    def _detail(self, page: int, action: str):
        return DetailCBD(
            action=action,
            item_id=str(self.item_id),
            key=self.key,
            api_page=self.api_page,
            page=page,
            next=page + 1,
            prev=page - 1,
            last=self.len
        ).pack()

    def detail(self, name: str, page: int, action: str):
        return self.btn_data(name, self._detail(page, action))

    def create_pagination_buttons(
            self, page: int, navigate: str, len_data: int, sub_page: Optional[int] = None, *args, **kwargs):
        if navigate == Navigation.first:
            self.add_button(
                self.pg(page).next_btn(1, self.increase(sub_page), *args, **kwargs)
            )
        elif navigate == Navigation.next:
            self.add_button(
                self.pg(page).prev_btn(-1, self.decrease(sub_page), *args, **kwargs)
            )
            if sub_page < len_data:
                self.add_button(
                    self.pg(page).next_btn(1, self.increase(sub_page), *args, **kwargs)
                )
        elif navigate == Navigation.prev:
            if sub_page > 1:
                self.add_button(
                    self.pg(page).prev_btn(-1, self.decrease(sub_page), *args, **kwargs)
                )
            self.add_button(
                self.pg(page).next_btn(1, self.increase(sub_page), *args, **kwargs)
            )
        self.add_markup(2 if len(self.get_kb()) == 2 else 1)
        return self
