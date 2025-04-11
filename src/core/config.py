import datetime
import json
import os
import sys
from pathlib import Path
from typing import Dict

from dotenv import load_dotenv
from pydantic import DirectoryPath, SecretStr, StrictStr
from pydantic_settings import BaseSettings

# DEFINE BASE DIR OA APP ###############################################################################################
BASE_DIR = Path(__file__).resolve(strict=True).parent.parent.parent
# DEFINE PATH TO .ENV FILE (DEPEND ON OS) ##############################################################################
ENV_FILE = ".env" if sys.platform == "win32" else ".env.docker"
ENV_PATH = str(Path(BASE_DIR).resolve(strict=True).joinpath(ENV_FILE))
load_dotenv(dotenv_path=ENV_PATH)

# MODE FOR REQUEST DATA BY API (save free API requests) ################################################################
# False from API AliExpress
# True from json files
FAKE_MODE = 1 == os.getenv("DB_NAME")
MODES = {
    True: f"🟨☢️ BOT START FAKE_MODE = {FAKE_MODE}",
    False: f"🟩🌐 BOT START FAKE_MODE = {FAKE_MODE}",
}
MODE_MASSAGE = MODES[FAKE_MODE]


def init_data_from_file(path: str, mode: str = "r"):
    with open(path, mode) as json_file:
        data = json.load(json_file)
        return data


# COUNTRIES' FLAGS (need for correct reviews) ##########################################################################
FLAGS = init_data_from_file("src/static/json/flags.json")

# TEXT AND CALLBACK DATA OF THE COMMON BUTTONS #########################################################################
KEYS = init_data_from_file("src/static/json/buttons.json")

# ALIEXPRESS API URLS ##################################################################################################
URL_API_ITEM_LIST = "item_search_5"
URL_API_ITEM_DETAIL = "item_detail_6"
URL_API_CATEGORY = "category_list_1"
URL_API_REVIEW = "item_review"

# DIRECTORY SETTINGS ###################################################################################################
STATIC_FOLDER = "static"
PRODUCT_IMAGE_FOLDER = "products"
DEFAULT_FOLDER = "default"
CACHE_FOLDER = "cache"
LOGGER_FOLDER = "logger"

# PATHS TO DIRECTORIES #################################################################################################
SRC_PATH = str(Path(BASE_DIR).resolve(strict=True).joinpath('src'))
STATIC_PATH = str(Path(SRC_PATH).resolve(strict=True).joinpath(STATIC_FOLDER))
IMAGE_PATH = str(Path(STATIC_PATH).resolve(strict=True).joinpath(PRODUCT_IMAGE_FOLDER))
CACHE_PATH = str(Path(STATIC_PATH).resolve(strict=True).joinpath(CACHE_FOLDER))
LOGGER_PATH = str(Path(SRC_PATH).resolve(strict=True).joinpath(LOGGER_FOLDER))

# LOCALES SETTINGS #####################################################################################################
LOCALE = "ru_RU"
CURRENCY = "RUB"
REGION = "RU"

RESULT_LIMIT = 5
MESSAGE_LIMIT = 1000

# IMAGE SETTINGS #######################################################################################################
WIDTH = 1024
HEIGHT = 576
THUMBNAIL = 500
IMG_FORMAT = "png"
IMG_LIMIT = 8

# SCHEDULER ############################################################################################################
SCHEDULE_RANGE = 1

# [PROD] CHECK MONITORING ITEMS EACH DAY IN DEFINED TIME (9:00 AM) #####################################################
MINUTES_AHEAD = 1
PRODUCTION_HOUR = 9
PRODUCTION_MINUTES = 0
# SCHEDULE_HOUR = PRODUCTION_HOUR  # 9
# SCHEDULE_MIN = PRODUCTION_MINUTES  # 0

# [DEV] CHECK MONITORING ITEMS SOME MINUTES AHEAD, AFTER START APP #####################################################
now = datetime.datetime.now()
future = now + datetime.timedelta(minutes=MINUTES_AHEAD)
SCHEDULE_HOUR = now.hour
SCHEDULE_MIN = future.minute

# REDIS (CACHE TIME IN REDIS MEMORY) ###################################################################################
CACHE_LIVE_TIME = 60 * 60 * 24  # 24 часа

# SORT SETTINGS ########################################################################################################
SORT_SET = {"default", "priceDesc", "priceAsc", "salesDesc"}
SORT_DICT = {
    "default": "по умолчанию",
    "priceDesc": "сначала дороже",
    "priceAsc": "сначала дешевле",
    "salesDesc": "по популярности",
}
SORT = {
    "default": "default",
    "desc": "priceDesc",
    "asc": "priceAsc",
    "sales": "salesDesc",
    "latest": "latest",
}
# QUANTITY SETTINGS (!DEPRECATED) ######################################################################################
QNT = {"2", "3", "5", "10"}

# DICT OF MAIN IMAGES ##################################################################################################
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
    "welcome": os.path.join(DEFAULT_FOLDER, "welcome_2.png"),
    "not_found": os.path.join(DEFAULT_FOLDER, "not_found.png"),
    "target": os.path.join(DEFAULT_FOLDER, "target.png"),
    "success": os.path.join(DEFAULT_FOLDER, "success_2.png"),
}
# HELPING TEXT IN `/help` ROUTE ########################################################################################
HELP = """
Бот умеет находить товары 
на популярном маркетплейсе `AliExpress`.
Товары можно добавлять в избранное.
А так же отслеживать изменение цен товаров
Бот реагирует на следующие команды:
▶️\t\t/start  начать работу с ботом
🏠\t\t/menu  главное меню
🛒\t\t/search  поиск товара
⭐️\t\t/favorite  избранные товары
📋\t\t/history  история просмотра
📊\t\t/monitor отслеживаемые товары
ℹ️\t\t/help справка
"""


class Settings(BaseSettings):
    """"""

    bot_token: SecretStr = os.getenv("BOT_TOKEN", None)
    api_key: SecretStr = os.getenv("API_KEY", None)

    host: StrictStr = os.getenv("HOST", None)
    base_url: StrictStr = os.getenv("URL", None)
    range: int = RESULT_LIMIT

    redis_host: StrictStr = os.getenv("REDIS_HOST")

    database: StrictStr = os.getenv("DB_NAME")
    db_user: StrictStr = os.getenv("DB_USER")
    db_host: StrictStr = os.getenv("DB_HOST", "localhost")
    db_port: StrictStr = os.getenv("DB_PORT")
    db_password: StrictStr = os.getenv("DB_PASS")

    headers: Dict = {
        "x-rapidapi-key": os.getenv("API_KEY", None),
        "x-rapidapi-host": os.getenv("HOST", None),
    }
    querystring: Dict = {
        "locale": LOCALE,
        "currency": CURRENCY,
        "region": REGION,
    }
    static_path: DirectoryPath = STATIC_PATH


conf = Settings()
