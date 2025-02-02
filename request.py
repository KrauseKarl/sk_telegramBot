import httpx

from config import settings


async def request_item_list(url, q=None, sort=None, cat_id=None) -> dict:
    base_url = settings.url
    full_url = base_url + "/" + url
    if q and sort:
        settings.querystring["q"] = q
        settings.querystring["sort"] = sort
    async with httpx.AsyncClient() as client:
        response = await client.get(
            url=full_url,
            headers=settings.headers,
            params=settings.querystring)
    return response.json()


async def request_item_detail(item_id: str):
    url = "item_detail_6"
    base_url = settings.url
    full_url = base_url + "/" + url
    settings.querystring["itemId"] = item_id
    async with httpx.AsyncClient() as client:
        response = await client.get(
            url=full_url,
            headers=settings.headers,
            params=settings.querystring)
    return response.json()