from api_telegram.keyboard.paginators import PaginationBtn


class HistoryPaginationBtn(PaginationBtn):
    def __init__(self, action, call_data):
        super().__init__(action, call_data)
        self.action = action
        self.page = 1
        self.call_data = call_data

    def _btn(self, num, navigate, *args, **kwargs):
        return self.call_data(
            action=self.action.paginate,
            navigate=navigate,
            page=self.__add__(num)
        ).pack()
