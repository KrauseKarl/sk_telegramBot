from api_telegram import FavoriteDeleteCBD
from api_telegram.keyboard.paginators import PaginationBtn


class FavoritePaginationBtn(PaginationBtn):
    def __init__(self, action, call_data, item_id):
        super().__init__(action, call_data, item_id)
        self.page = 1
        self.item_id = item_id
        self.action = action
        self.call_data = call_data

    def _btn(self, num: int, navigate: str, *args, **kwargs):
        return self.call_data(
            action=self.action.paginate,
            navigate=navigate,
            page=self.__add__(num),
            item_id=self.item_id
        ).pack()

    def next_btn(self, num: int = 1, *args, **kwargs):  # page + 1
        return self.btn_data(
            name='next',
            data=self._btn(num, self.navigate.next, *args, **kwargs)
        )

    def prev_btn(self, num: int = -1, *args, **kwargs):  # page - 1
        return self.btn_data(
            name='prev',
            data=self._btn(num, self.navigate.prev, *args, **kwargs)
        )

    def delete_btn(self, navigate, item_id=None):
        return self.btn_data(
            name='delete',
            data=FavoriteDeleteCBD(
                action=self.action.delete,
                navigate=navigate,
                item_id=self.item_id,
                page=self.page
            ).pack()
        )
