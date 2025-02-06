import os
from typing import Dict
from pathlib import Path
from dotenv import load_dotenv
from pydantic import SecretStr, StrictStr, DirectoryPath
from pydantic_settings import BaseSettings

load_dotenv()

BASE_DIR = Path(__file__).resolve(strict=True).parent
STATIC_PATH = str(Path(BASE_DIR).resolve(strict=True).joinpath("static"))
# DATETIME_FORMAT = '%d.%m.%Y - %H:%M:%S'
# DEFAULT_COMMANDS = (
#     ('start', 'Начало работы'),
#     ('help', 'Информация по командам'),
#     ('low', 'Товары/услуги по минимальным характеристикам поиска'),
#     ('high', 'Товары/услуги по максимальным характеристикам поиска'),
#     ('custom', 'Товары/услуги по настраиваемым характеристикам поиска'),
#     ('history', 'История поиска'),
# )
# RESULT_LIMIT = 15
SORT = {
    "default": "default",
    "desc": "priceDesc",
    "asc": "priceAsc",
    "sales": "salesDesc",
    "latest": "latest",
}
SORT_SET = {
    "default",
    "priceDesc",
    "priceAsc",
    "salesDesc"
}
BTNS = {"2", "3", "5", "10"}


class Settings(BaseSettings):
    """"""

    bot_token: SecretStr = os.getenv("BOT_TOKEN", None)
    api_key: SecretStr = os.getenv("API_KEY", None)

    host: StrictStr = os.getenv("HOST", None)
    url: StrictStr = os.getenv("URL", None)
    range: int = 5

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
        "locale": "ru_RU",
        "currency": "RUB",
        "region": "RU",
    }
    static_path: DirectoryPath = STATIC_PATH

conf = Settings()
