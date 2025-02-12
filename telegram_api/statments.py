from aiogram.fsm import state


class ItemFSM(state.StatesGroup):
    """Группа состояний."""

    product = state.State()
    qnt = state.State()
    sort = state.State()


class CategoryFSM(state.StatesGroup):
    """Группа состояний."""

    name = state.State()
    cat_id = state.State()
    product = state.State()
    qnt = state.State()
    sort = state.State()


class FavoriteFSM(state.StatesGroup):
    """Группа состояний."""

    product_id = state.State()
    title = state.State()
    price = state.State()
    reviews = state.State()
    stars = state.State()
    url = state.State()
    image = state.State()
