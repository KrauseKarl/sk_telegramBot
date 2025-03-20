from api_telegram.callback_data import DetailAction, MonitorAction, MonitorCBD
from api_telegram.keyboards import ItemPaginationBtn
from database.orm import orm_get_monitoring_item, orm_get_favorite


async def kb_factory_detailItem_page(callback_data):

    kb = ItemPaginationBtn(
        key=callback_data.key,
        api_page=callback_data.api_page,
        item_id=callback_data.item_id,
        paginator_len=int(callback_data.last)
    )

    kb.add_buttons([
        kb.comment(callback_data.page),
        kb.images(callback_data.page),
        # kb.btn_text('price'),
        kb.detail('back', callback_data.page, DetailAction.back_list),

    ])
    is_monitoring = await orm_get_monitoring_item(callback_data.item_id)
    if is_monitoring is None:
        data = MonitorCBD(
            action=MonitorAction.add,
            item_id=callback_data.item_id
        ).pack()
        kb.btn_data("price", data)
    is_favorite = await orm_get_favorite(item_id=callback_data.item_id)
    if is_favorite is None:
        kb.add_button(kb.favorite(callback_data.page))
    kb.add_markups([2, 2, 1])
