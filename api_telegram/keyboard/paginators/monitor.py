from typing import Optional

from api_telegram.keyboard.paginators import PaginationBtn


class MonitorPaginationBtn(PaginationBtn):
    def __init__(self, item_id, action, call_data):
        super().__init__(item_id, action, call_data)
        self.page = 1
        self.item_id = item_id
        self.action = action
        self.call_data = call_data

    def _btn(
            self,
            navigate: str,
            action: Optional[str] = None,
            num: Optional[int] = None,
            *args,
            **kwargs
    ):
        super()._btn(num=num, navigate=navigate, action=action, *args, **kwargs)
        return self.call_data(
            action=action,
            navigate=navigate,
            item_id=self.item_id,
            page=self.__add__(num)
        ).pack()

    def delete_btn(self, navigate: str):
        return self.btn_data(
            'delete',
            self._btn(
                navigate=navigate,
                action=self.action.delete,
                item_id=self.item_id
            )
        )

    def graph_btn(self, navigate: str):
        data = self._btn(
            navigate=navigate,
            action=self.action.graph,
            item_id=self.item_id
        )
        return self.btn_data('graph', data)

    def target_btn(self, navigate: str):
        data = self._btn(
            navigate=navigate,
            action=self.action.target,
            item_id=self.item_id
        )
        return self.btn_data('target', data)
