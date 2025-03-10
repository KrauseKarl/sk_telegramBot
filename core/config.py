import datetime
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
FLAGS = {
    "BD": "Bangladesh", "BE": "Belgium", "BF": "Burkina Faso", "BG": "Bulgaria", "BA": "Bosnia and Herzegovina",
    "BB": "Barbados", "WF": "Wallis and Futuna", "BL": "Saint Barthelemy", "BM": "Bermuda", "BN": "Brunei",
    "BO": "Bolivia", "BH": "Bahrain", "BI": "Burundi", "BJ": "Benin", "BT": "Bhutan", "JM": "Jamaica",
    "BV": "Bouvet Island", "BW": "Botswana", "WS": "Samoa", "BQ": "Bonaire, Saint Eustatius and Saba ", "BR": "Brazil",
    "BS": "Bahamas", "JE": "Jersey", "BY": "Belarus", "BZ": "Belize", "RU": "Russia", "RW": "Rwanda", "RS": "Serbia",
    "TL": "East Timor", "RE": "Reunion", "TM": "Turkmenistan", "TJ": "Tajikistan", "RO": "Romania", "TK": "Tokelau",
    "GW": "Guinea-Bissau", "GU": "Guam", "GT": "Guatemala", "GS": "South Georgia and the South Sandwich Islands",
    "GR": "Greece", "GQ": "Equatorial Guinea", "GP": "Guadeloupe", "JP": "Japan", "GY": "Guyana", "GG": "Guernsey",
    "GF": "French Guiana", "GE": "Georgia", "GD": "Grenada", "UK": "United Kingdom", "GA": "Gabon",
    "SV": "El Salvador", "GN": "Guinea", "GM": "Gambia", "GL": "Greenland", "GI": "Gibraltar", "GH": "Ghana",
    "OM": "Oman", "TN": "Tunisia", "JO": "Jordan", "HR": "Croatia", "HT": "Haiti", "HU": "Hungary", "HK": "Hong Kong",
    "HN": "Honduras", "HM": "Heard Island and McDonald Islands", "VE": "Venezuela", "PR": "Puerto Rico",
    "PS": "Palestinian Territory", "PW": "Palau", "PT": "Portugal", "SJ": "Svalbard and Jan Mayen", "PY": "Paraguay",
    "IQ": "Iraq", "PA": "Panama", "PF": "French Polynesia", "PG": "Papua New Guinea", "PE": "Peru", "PK": "Pakistan",
    "PH": "Philippines", "PN": "Pitcairn", "PL": "Poland", "PM": "Saint Pierre and Miquelon", "ZM": "Zambia",
    "EH": "Western Sahara", "EE": "Estonia", "EG": "Egypt", "ZA": "South Africa", "EC": "Ecuador", "IT": "Italy",
    "VN": "Vietnam", "SB": "Solomon Islands", "ET": "Ethiopia", "SO": "Somalia", "ZW": "Zimbabwe",
    "SA": "Saudi Arabia", "ES": "Spain", "ER": "Eritrea", "ME": "Montenegro", "MD": "Moldova", "MG": "Madagascar",
    "MF": "Saint Martin", "MA": "Morocco", "MC": "Monaco", "UZ": "Uzbekistan", "MM": "Myanmar", "ML": "Mali",
    "MO": "Macao", "MN": "Mongolia", "MH": "Marshall Islands", "MK": "Macedonia", "MU": "Mauritius", "MT": "Malta",
    "MW": "Malawi", "MV": "Maldives", "MQ": "Martinique", "MP": "Northern Mariana Islands", "MS": "Montserrat",
    "MR": "Mauritania", "IM": "Isle of Man", "UG": "Uganda", "TZ": "Tanzania", "MY": "Malaysia", "MX": "Mexico",
    "IL": "Israel", "FR": "France", "IO": "British Indian Ocean Territory", "SH": "Saint Helena", "FI": "Finland",
    "FJ": "Fiji", "FK": "Falkland Islands", "FM": "Micronesia", "FO": "Faroe Islands", "NI": "Nicaragua",
    "NL": "Netherlands", "NO": "Norway", "NA": "Namibia", "VU": "Vanuatu", "NC": "New Caledonia", "NE": "Niger",
    "NF": "Norfolk Island", "NG": "Nigeria", "NZ": "New Zealand", "NP": "Nepal", "NR": "Nauru", "NU": "Niue",
    "CK": "Cook Islands", "XK": "Kosovo", "CI": "Ivory Coast", "CH": "Switzerland", "CO": "Colombia", "CN": "China",
    "CM": "Cameroon", "CL": "Chile", "CC": "Cocos Islands", "CA": "Canada", "CG": "Republic of the Congo",
    "CF": "Central African Republic", "CD": "Democratic Republic of the Congo", "CZ": "Czech Republic", "CY": "Cyprus",
    "CX": "Christmas Island", "CR": "Costa Rica", "CW": "Curacao", "CV": "Cape Verde", "CU": "Cuba", "SZ": "Swaziland",
    "SY": "Syria", "SX": "Sint Maarten", "KG": "Kyrgyzstan", "KE": "Kenya", "SS": "South Sudan", "SR": "Suriname",
    "KI": "Kiribati", "KH": "Cambodia", "KN": "Saint Kitts and Nevis", "KM": "Comoros", "ST": "Sao Tome and Principe",
    "SK": "Slovakia", "KR": "South Korea", "SI": "Slovenia", "KP": "North Korea", "KW": "Kuwait", "SN": "Senegal",
    "SM": "San Marino", "SL": "Sierra Leone", "SC": "Seychelles", "KZ": "Kazakhstan", "KY": "Cayman Islands",
    "SG": "Singapore", "SE": "Sweden", "SD": "Sudan", "DO": "Dominican Republic", "DM": "Dominica", "DJ": "Djibouti",
    "DK": "Denmark", "VG": "British Virgin Islands", "DE": "Germany", "YE": "Yemen", "DZ": "Algeria",
    "US": "United States", "UY": "Uruguay", "YT": "Mayotte", "UM": "United States Minor Outlying Islands",
    "LB": "Lebanon", "LC": "Saint Lucia", "LA": "Laos", "TV": "Tuvalu", "TW": "Taiwan", "TT": "Trinidad and Tobago",
    "TR": "Turkey", "LK": "Sri Lanka", "LI": "Liechtenstein", "LV": "Latvia", "TO": "Tonga", "LT": "Lithuania",
    "LU": "Luxembourg", "LR": "Liberia", "LS": "Lesotho", "TH": "Thailand", "TF": "French Southern Territories",
    "TG": "Togo", "TD": "Chad", "TC": "Turks and Caicos Islands", "LY": "Libya", "VA": "Vatican",
    "VC": "Saint Vincent and the Grenadines", "AE": "United Arab Emirates", "AD": "Andorra",
    "AG": "Antigua and Barbuda", "AF": "Afghanistan", "AI": "Anguilla", "VI": "U.S. Virgin Islands", "IS": "Iceland",
    "IR": "Iran", "AM": "Armenia", "AL": "Albania", "AO": "Angola", "AQ": "Antarctica", "AS": "American Samoa",
    "AR": "Argentina", "AU": "Australia", "AT": "Austria", "AW": "Aruba", "IN": "India", "AX": "Aland Islands",
    "AZ": "Azerbaijan", "IE": "Ireland", "ID": "Indonesia", "UA": "Ukraine", "QA": "Qatar", "MZ": "Mozambique"
}


load_dotenv()

FAKE_MODE = 1 == 0

# ALIEXPRESS API URLS ###################################################################
URL_API_ITEM_LIST = "item_search_5"
URL_API_ITEM_DETAIL = "item_detail_6"
URL_API_CATEGORY = "category_list_1"
URL_API_REVIEW = "item_review"


# DIRECTORY SETTINGS ####################################################################
STATIC_FOLDER = 'static'
PRODUCT_IMAGE_FOLDER = 'products'
DEFAULT_FOLDER = 'default'
CACHE_FOLDER = "cache"

# PATHS TO DIRECTORIES ###################################################################
BASE_DIR = Path(__file__).resolve(strict=True).parent.parent
STATIC_PATH = str(Path(BASE_DIR).resolve(strict=True).joinpath(STATIC_FOLDER))
IMAGE_PATH = str(Path(STATIC_PATH).resolve(strict=True).joinpath(PRODUCT_IMAGE_FOLDER))
CACHE_PATH = str(Path(STATIC_PATH).resolve(strict=True).joinpath(CACHE_FOLDER))

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

# SCHEDULER ################################################################################
now = datetime.datetime.now()
future = now + datetime.timedelta(minutes=2)

SCHEDULE_HOUR = now.hour
SCHEDULE_MIN = future.minute

# REDIS ####################################################################################
CACHE_LIVE_TIME = 60 * 60 * 24  # 24 часа

# SORT SETTINGS ############################################################################
SORT_SET = {"default", "priceDesc", "priceAsc", "salesDesc"}
SORT_DICT = {
    "default": "по умолчанию",
    "priceDesc": "сначала дороже",
    "priceAsc": "сначала дешевле",
    "salesDesc": "по популярности",
}
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
    "welcome": os.path.join(DEFAULT_FOLDER, "welcome_2.png"),
    "not_found": os.path.join(DEFAULT_FOLDER, "not_found.png"),
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
