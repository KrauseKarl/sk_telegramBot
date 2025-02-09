from aiogram.fsm.state import State, StatesGroup


class Form(StatesGroup):
    """Группа состояний."""

    product = State()
    qnt = State()
    sort = State()


class CategoryForm(StatesGroup):
    """Группа состояний."""

    name = State()
    cat_id = State()
    product = State()
    qnt = State()
    sort = State()


class FavoriteForm(StatesGroup):
    """Группа состояний."""

    product_id = State()
    title = State()
    price = State()
    reviews = State()
    stars = State()
    url = State()
    image = State()

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
