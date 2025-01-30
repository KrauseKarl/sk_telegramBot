import random
import time

import requests
from requests import RequestException
from bs4 import BeautifulSoup

from scaper_api.uri_list import auto_url_list


class Scraper:
    def __init__(self, url, tag, class_name):
        self.url = url
        self.tag = tag
        self.class_name = class_name

    def get_response(self):
        try:
            res = requests.get(self.url)
            return res.content
        except RequestException as err:
            print(err)
            return None

    def get_class(self):
        try:
            html_content = self.get_response()
            soup = BeautifulSoup(html_content, 'html.parser')
            div = soup.find(self.tag, class_=self.class_name).g
            return div.getText()
        except Exception as err:
            print( err)
            return None


def get_response(url: str):
    try:
        res = requests.get(url)
        return res.content
    except RequestException as err:
        print(__name__, err)
        return None


def get_class(html_content: str, name: str, div_class: str) -> str | None:
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        div = soup.find(name, class_=div_class)
        return div.getText()
    except Exception as err:
        print(__name__, err)
        return None


def get_meta(html_content: str):
    try:
        name_result = None
        class_result = None
        soup = BeautifulSoup(html_content, 'html.parser')
        brand_ = soup.find(itemprop="brand").get("content")

        images_ = soup.find_all('img', attrs={"itemprop": "image"})
        print(f'\n{images_= }\n')
        prices = soup.find_all('meta', attrs={"itemprop": "price"})
        prices_ = sorted(set([pr.get("content") for pr in prices]))

        discount_ = prices_[1]
        try:
            price_ = prices_[2]
        except Exception:
            price_ = prices_[1]

        spans = soup.find_all(name="span", attrs={"itemprop": "name"})

        for span in spans:
            s = str(span).split("<span ")[1]
            if s.startswith("class"):
                name_result = span.getText().strip()
                l_split = s.split('class=\"')[1]
                class_result = l_split.split("\" i")[0]
        # print(f'{name_result= } {class_result= }')

        name_ = name_result
        class_ = class_result

        return brand_, name_, price_, class_, discount_
    except Exception as err:
        print(err)
        return None


def scraper_div(div_class: str, tag_name: str, url_list: list):
    for ur in url_list:
        # scraper = Scraper(url=ur, tag=tag_name, class_name=div_class)
        # print(scraper.get_class())
        html_ = get_response(ur)
        div = get_class(html_, tag_name, div_class)
        print(div)
        time.sleep(random.randint(2, 3))


def scraper_golden_apple(site_url):
    class_list = []

    for ur in site_url:
        site_url = ur  # input('url: ')
        response = get_response(site_url)
        try:
            brand, name, price, _class_, discount = get_meta(response)
            print(f"{brand} '{name}' {discount} ₽ [{price} ₽]\t\t\t[{_class_}]")
            if _class_ not in class_list:
                class_list.append(_class_)
        except Exception as err:
            print(f"! {err}")
        sleep_time = random.randint(1, 7)
        time.sleep(sleep_time)

    print(class_list)


if __name__ == '__main__':
    ...
    # scraper_div(div_class="wb9m8q0", tag_name="div", url_list=dron_url_list)

    # scraper_div(div_class="OfferPriceCaption__price", tag_name="div", url_list=auto_url_list)

    # scraper_golden_apple(site_url=golden_apple_url_list)
