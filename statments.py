from aiogram.fsm.state import State, StatesGroup


class Form(StatesGroup):
    """Группа состояний."""

    product = State()
    qnt = State()
    sort = State()


class CategoryForm(StatesGroup):
    """Группа состояний."""

    name = State()

# class UserState(StatesGroup):
#     """Группа состояний."""
#
#     low_prod_name = State()
#     low_result_size = State()
#     high_prod_name = State()
#     high_result_size = State()
#     custom_prod_name = State()
#     custom_price_range = State()
#     custom_result_size = State()
