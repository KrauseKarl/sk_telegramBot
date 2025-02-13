import os
from pathlib import Path
from typing import Dict

from dotenv import load_dotenv
from pydantic import DirectoryPath, SecretStr, StrictStr
from pydantic_settings import BaseSettings

# DEFAULT_COMMANDS = (
#     ('start', 'Начало работы'),
#     ('help', 'Информация по командам'),
#     ('low', 'Товары/услуги по минимальным характеристикам поиска'),
#     ('high', 'Товары/услуги по максимальным характеристикам поиска'),
#     ('custom', 'Товары/услуги по настраиваемым характеристикам поиска'),
#     ('history', 'История поиска'),
# )

load_dotenv()

# ALIEXPRESS API URLS ###################################################################
URL_API_ITEM_LIST = "item_search_5"
URL_API_ITEM_DETAIL = "item_detail_6"
URL_API_CATEGORY = "category_list_1"

# DIRECTORY SETTINGS ####################################################################
STATIC_FOLDER = 'static'
PRODUCT_IMAGE_FOLDER = 'products'
DEFAULT_FOLDER = 'default'

# PATHS TO DIRECTORIES ###################################################################
BASE_DIR = Path(__file__).resolve(strict=True).parent.parent
STATIC_PATH = str(Path(BASE_DIR).resolve(strict=True).joinpath(STATIC_FOLDER))
IMAGE_PATH = str(Path(STATIC_PATH).resolve(strict=True).joinpath(PRODUCT_IMAGE_FOLDER))

# LOCALES SETTINGS #######################################################################
LOCALE = "ru_RU"
CURRENCY = "RUB"
REGION = "RU"

RESULT_LIMIT = 5
MESSAGE_LIMIT = 1000

# IMAGE SETTINGS ##########################################################################
WIDTH = 1024
HEIGHT = 576
THUMBNAIL = 500
IMG_FORMAT = "png"
IMG_LIMIT = 8

# SORT SETTINGS ############################################################################
SORT_SET = {"default", "priceDesc", "priceAsc", "salesDesc"}

QNT = {"2", "3", "5", "10"}

SORT = {
    "default": "default",
    "desc": "priceDesc",
    "asc": "priceAsc",
    "sales": "salesDesc",
    "latest": "latest",
}
HERO = {
    "category": os.path.join(DEFAULT_FOLDER, "category_2.png"),
    "error": os.path.join(DEFAULT_FOLDER, "error_2.png"),
    "favorite": os.path.join(DEFAULT_FOLDER, "favorites_2.png"),
    "help": os.path.join(DEFAULT_FOLDER, "help_2.png"),
    "history": os.path.join(DEFAULT_FOLDER, "history_2.png"),
    "menu": os.path.join(DEFAULT_FOLDER, "menu_2.png"),
    "price_min": os.path.join(DEFAULT_FOLDER, "price_min_2.png"),
    "price_max": os.path.join(DEFAULT_FOLDER, "price_max_2.png"),
    "range": os.path.join(DEFAULT_FOLDER, "range_2.png"),
    "quantity": os.path.join(DEFAULT_FOLDER, "quantity_2.png"),
    "sort": os.path.join(DEFAULT_FOLDER, "sort_2.png"),
    "search": os.path.join(DEFAULT_FOLDER, "search_2.png"),
    "result": os.path.join(DEFAULT_FOLDER, "result_2.png"),
}


class Settings(BaseSettings):
    """"""

    bot_token: SecretStr = os.getenv("BOT_TOKEN", None)
    api_key: SecretStr = os.getenv("API_KEY", None)

    host: StrictStr = os.getenv("HOST", None)
    base_url: StrictStr = os.getenv("URL", None)
    range: int = RESULT_LIMIT

    database: StrictStr = os.getenv("DB_NAME")
    db_user: StrictStr = os.getenv("DB_USER")
    db_host: StrictStr = os.getenv("DB_HOST")
    db_port: StrictStr = os.getenv("DB_PORT")
    db_password: StrictStr = os.getenv("DB_PASS")

    headers: Dict = {
        "x-rapidapi-key": os.getenv("API_KEY", None),
        "x-rapidapi-host": os.getenv("HOST", None)
    }
    querystring: Dict = {
        "locale": LOCALE,
        "currency": CURRENCY,
        "region": REGION,
    }
    static_path: DirectoryPath = STATIC_PATH


conf = Settings()
