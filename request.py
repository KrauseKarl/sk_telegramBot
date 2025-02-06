import httpx

from config import conf


async def request_item_list(url, q=None, sort=None, cat_id=None) -> dict:
    base_url = conf.url
    full_url = base_url + "/" + url
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
    url = "item_detail_6"
    base_url = conf.url
    full_url = base_url + "/" + url
    conf.querystring["itemId"] = item_id
    async with httpx.AsyncClient() as client:
        response = await client.get(
            url=full_url,
            headers=conf.headers,
            params=conf.querystring)
    return response.json()