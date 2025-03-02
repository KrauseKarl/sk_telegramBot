
from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm import state

from api_aliexpress.request import *
from api_redis.handlers import *
from api_telegram.callback_data import *
from api_telegram.keyboards import *
from core.config import conf
from database.paginator import *
from utils.media import *
from utils.message_info import *

review = Router()


class Review(state.StatesGroup):
    product = state.State()


async def save_data_json_local(data, item_id: str = None, folder: str = None):
    file_name = "{0}.json".format(item_id.lower())
    file_path = os.path.join(
        config.BASE_DIR,
        "_json_example",
        folder,
        file_name
    )
    with open(file_path, "w") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)


# "/item_review?
# itemId        =1005006898150255
# page          =1
# sort          =latest
# filter        =allReviews

async def request_api_review(
        url: str = None,
        page: str = None,
        item_id: str = None,
        sort: str = None,
        filter: str = None

) -> dict:

    full_url = "/".join([conf.base_url, url])
    if item_id:
        conf.querystring["itemId"] = item_id
    if sort:
        conf.querystring["sort"] = sort
    if page:
        conf.querystring["page"] = page
    if filter:
        conf.querystring["filter"] = filter

    async with httpx.AsyncClient() as client:
        response = await client.get(
            url=full_url,
            headers=conf.headers,
            params=conf.querystring
        )
    result = response.json()
    if item_id:
        await save_data_json(data=result, item_id=item_id, folder=REVIEW_FAKE_FOLDER)

    return result


@review.callback_query(ReviewCBD.filter(F.action.in_({RevAction.first, RevAction.page})))
async def request_review(callback: CallbackQuery, callback_data: ReviewCBD):
    try:
        item_id = callback_data.item_id
        key = callback_data.key
        page = int(callback_data.page)
        api_page = int(callback_data.api_page)
        navigate = callback_data.navigate
        review_page = callback_data.review_page

        cache_key = CacheKey(key=key, api_page=api_page, extra='review').pack()
        review_list_cache = await redis_get_data_from_cache(cache_key)

        if review_list_cache is None:
            ################################################################################
            # FAKE_MODE                                                                    #
            ################################################################################
            if config.FAKE_MODE:
                my_file = Path(
                    os.path.join(
                        config.BASE_DIR,
                        FAKE_MAIN_FOLDER,
                        REVIEW_FAKE_FOLDER,
                        "review_{0}.json".format(item_id)
                    )
                )
                if my_file.is_file():
                    print('FAKE_MODE request from 🟩🟩🟩 FILE')
                    response = await request_api_review_fake(item_id=item_id)
                else:
                    print('FAKE_MODE request from 🟥🟥🟥 INTERNET')
                    response = await request_api_review(
                        url=config.URL_API_REVIEW,
                        page=str(api_page),
                        item_id=item_id,
                        sort="latest",
                        filter="allReviews"
                    )
            else:
                ################################################################################
                print(f"🌐🌐🌐🟥 DATA FROM INTERNET [💬 REVIEW]")
                response = await request_api_review(
                    url=config.URL_API_REVIEW,
                    page=str(api_page),
                    item_id=item_id,
                    sort="latest",
                    filter="allReviews"
                )
            try:
                review_list_cache = response['result']['resultList']
                await redis_set_data_to_cache(key=cache_key, value=review_list_cache)
            except KeyError:
                review_list_cache = response['data']
        if review_list_cache != 'error':
            if api_page == 0 or page > len(review_list_cache):
                api_page += 1
                page = 1
                cache_data = await redis_get_data_from_cache(cache_key)
                if cache_data is None:
                    await redis_set_data_to_cache(key=cache_key, value=review_list_cache)

            paginator = Paginator(array=review_list_cache, page=int(review_page))
            reviews = paginator.get_page()[0]
            msg = await create_review_tg_answer(reviews, review_page, paginator.len)
            print('\n*****', reviews['review']['reviewImages'])
            # todo make func `simple paginator`
            kb = RevPaginationBtn(
                key=key,
                api_page=api_page,
                item_id=item_id,
                paginator_len=callback_data.last
            )
            if paginator.len > 1:
                if navigate == RevNavigate.first:
                    kb.add_button(kb.next_btn(page, int(review_page) + 1)).add_markup(1)
                elif navigate == RevNavigate.next:
                    kb.add_button(kb.prev_btn(page, int(review_page) - 1)).add_markup(2)
                    if int(review_page) < paginator.len:
                        kb.add_button(kb.next_btn(page, int(review_page) + 1)).add_markup(2)
                elif navigate == RevNavigate.prev:
                    if int(review_page) > 1:
                        kb.add_button(kb.prev_btn(page, int(review_page) - 1)).add_markup(2)
                    kb.add_button(kb.next_btn(page, int(review_page) + 1)).add_markup(2)

            back_button = kb.detail("back", page, DetailAction.back_detail)
            kb.add_button(back_button).add_markups([1])
            # todo make func `simple paginator`
            try:
                media = ":".join(["https", reviews['review']['reviewImages'][0]])
                photo = types.InputMediaPhoto(media=media, caption=msg)
            except:
                media = await get_fs_input_hero_image('result')
                photo = types.InputMediaPhoto(media=media, caption=msg)
            await callback.message.edit_media(media=photo, reply_markup=kb.create_kb())
        else:
            kb = ItemPaginationBtn(
                key=callback_data.key,
                api_page=callback_data.api_page,
                paginator_len=callback_data.last,
                item_id=callback_data.item_id
            )
            back_call_back = kb.detail('back', callback_data.page, DetailAction.back_detail)
            kb.add_button(back_call_back).add_markup(1)
            media = await get_fs_input_hero_image('not_found')
            photo = types.InputMediaPhoto(media=media, caption='⭕️ нет комментариев')
            await callback.message.edit_media(media=photo, reply_markup=kb.create_kb())
    except Exception as error:
        print(str(error))
        await callback.answer(text=f'⚠️ error review')
