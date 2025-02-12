import httpx

from core import config
from core.config import conf


async def request_api(
        url: str,
        query=None,
        sort=None,
        cat_id=None,
        start_price=None,
        end_price=None
) -> dict:
    full_url = "/".join([conf.base_url, url])

    if query:
        conf.querystring["q"] = query
    if sort:
        conf.querystring["sort"] = sort
    if cat_id:
        conf.querystring["catId"] = str(cat_id)
    if start_price:
        conf.querystring["startPrice"] = start_price
    if end_price:
        conf.querystring["endPrice"] = end_price
    print(conf.querystring.items())
    async with httpx.AsyncClient() as client:
        response = await client.get(
            url=full_url,
            headers=conf.headers,
            params=conf.querystring
        )

    return response.json()


async def request_item_list(url: str, q=None, sort=None, cat_id=None) -> dict:
    full_url = "/".join([conf.base_url, url])
    print(full_url)
    if q and sort:
        conf.querystring["q"] = q
        conf.querystring["sort"] = sort
    async with httpx.AsyncClient() as client:
        response = await client.get(
            url=full_url,
            headers=conf.headers,
            params=conf.querystring)
    return response.json()


async def request_item_detail(item_id: str) -> dict:
    url = config.URL_API_ITEM_DETAIL
    base_url = conf.base_url
    full_url = base_url + "/" + url
    conf.querystring["itemId"] = item_id
    async with httpx.AsyncClient() as client:
        response = await client.get(
            url=full_url,
            headers=conf.headers,
            params=conf.querystring)
    return response.json()
