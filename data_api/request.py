import httpx

from core import config
from core.config import conf
from database.exceptions import FreeAPIExceededError


async def request_api(
        url: str = None,
        page: str = None,
        item_id: str = None,
        query: str = None,
        sort: str = None,
        cat_id: str = None,
        start_price: str = None,
        end_price: str = None,

) -> dict:
    full_url = "/".join([conf.base_url, url])

    if query:
        conf.querystring["q"] = query
    if item_id:
        conf.querystring["itemId"] = item_id
    if sort:
        conf.querystring["sort"] = sort
    if cat_id:
        conf.querystring["catId"] = str(cat_id)
    if start_price:
        conf.querystring["startPrice"] = start_price
    if end_price:
        conf.querystring["endPrice"] = end_price
    if page:
        conf.querystring["page"] = page

    # todo delete after develop
    print("☀️" * 10)
    print("REQUEST TO ALIEXPRESS API - {}".format(conf.querystring.items()))
    print("☀️" * 10)
    # todo delete after develop
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                url=full_url,
                headers=conf.headers,
                params=conf.querystring
            )
        result = response.json()
    except httpx.ReadTimeout as error:
        raise FreeAPIExceededError(
            message="HTTP ERROR\n{0}".format(error)
        )

    if "message" in result:
        print(f"❌❌❌ лимит API превышен")
        raise FreeAPIExceededError(
            message="❌ лимит API превышен\n{0}".format(
                result.get('message')
            )
        )
    print(f"✅✅✅ лимит API в норме")
    return result

# async def request_item_list(url: str, q=None, sort=None, cat_id=None) -> dict:
#     full_url = "/".join([conf.base_url, url])
#     print(full_url)
#     if q and sort:
#         conf.querystring["q"] = q
#         conf.querystring["sort"] = sort
#     async with httpx.AsyncClient() as client:
#         response = await client.get(
#             url=full_url,
#             headers=conf.headers,
#             params=conf.querystring)
#     return response.json()
#
#
# async def request_item_detail(item_id: str) -> dict:
#     url = config.URL_API_ITEM_DETAIL
#     base_url = conf.base_url
#     full_url = base_url + "/" + url
#     conf.querystring["itemId"] = item_id
#     async with httpx.AsyncClient() as client:
#         response = await client.get(
#             url=full_url,
#             headers=conf.headers,
#             params=conf.querystring)
#     result = response.json()
#     print(f"{'message' in result= }")
#     if "message" in result:
#         raise FreeAPIExceededError(
#             message="❌ лимит API превышен\n{0}".format(
#                 result.get('message')
#             )
#         )
#     return response.json()
