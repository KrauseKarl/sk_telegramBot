from aiogram.fsm import state


class ItemFSM(state.StatesGroup):
    """Группа состояний поиска товара."""

    product = state.State()
    price_min = state.State()
    price_max = state.State()
    qnt = state.State()
    sort = state.State()


class TargetFSM(state.StatesGroup):
    """Группа состояний целевой цены для мониторинга товара."""

    product_id = state.State()
    callback = state.State()
    price = state.State()
