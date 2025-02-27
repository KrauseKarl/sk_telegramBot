import json
import os
import emoji
import httpx
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from aiogram.fsm import state

from core import config
from core.config import conf

review = Router()


class Review(state.StatesGroup):
    product = state.State()


async def save_data_json(data, item_id: str = None):
    file_name = "{0}.json".format(item_id.lower())
    file_path = os.path.join(
        config.BASE_DIR,
        "_json_example",
        "_reviews",
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
    print(f"{full_url= }")
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
        await save_data_json(data=result, item_id=item_id)

    return result


@review.callback_query(F.data.startswith("review"))
async def request_review(message: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(Review.product)
    await message.message.answer('💬💬💬 Введите артикул товара')


COUNTRY_FLAGS = {
    "BD": "Bangladesh", "BE": "Belgium", "BF": "Burkina Faso", "BG": "Bulgaria", "BA": "Bosnia and Herzegovina",
    "BB": "Barbados", "WF": "Wallis and Futuna", "BL": "Saint Barthelemy", "BM": "Bermuda", "BN": "Brunei",
    "BO": "Bolivia", "BH": "Bahrain", "BI": "Burundi", "BJ": "Benin", "BT": "Bhutan", "JM": "Jamaica",
    "BV": "Bouvet Island", "BW": "Botswana", "WS": "Samoa", "BQ": "Bonaire, Saint Eustatius and Saba ", "BR": "Brazil",
    "BS": "Bahamas", "JE": "Jersey", "BY": "Belarus", "BZ": "Belize", "RU": "Russia", "RW": "Rwanda", "RS": "Serbia",
    "TL": "East Timor", "RE": "Reunion", "TM": "Turkmenistan", "TJ": "Tajikistan", "RO": "Romania", "TK": "Tokelau",
    "GW": "Guinea-Bissau", "GU": "Guam", "GT": "Guatemala", "GS": "South Georgia and the South Sandwich Islands",
    "GR": "Greece", "GQ": "Equatorial Guinea", "GP": "Guadeloupe", "JP": "Japan", "GY": "Guyana", "GG": "Guernsey",
    "GF": "French Guiana", "GE": "Georgia", "GD": "Grenada", "GB": "United Kingdom", "GA": "Gabon",
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
    "US": "United_States", "UY": "Uruguay", "YT": "Mayotte", "UM": "United States Minor Outlying Islands",
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

@review.message(Review.product)
async def request_product_name(message: Message, state: FSMContext) -> None:
    await state.update_data(product=message.text)
    response = await request_api_review(
        item_id=message.text,
        sort="latest",
        url=config.URL_API_REVIEW,
        page='1',
        filter="allReviews"
    )
    reviews = response['result']['resultList'][:20]
    print(emoji.demojize("🇺🇸"))
    print(emoji.demojize("🏴‍☠️"))
    for r in reviews:
        dtime = r['review']['reviewDate']
        stars = r['review']['reviewStarts']
        item_title = r['review']['itemSpecInfo']
        try:
            review_text = r.get('review').get('translation').get('reviewContent', 'no comment')
        except KeyError:
            review_text = '---'
        msg = "{0}\n".format("⭐️" * stars)
        msg += '{0}\n'.format(dtime)
        msg += "<i>{0:.200}</i>\n\n".format(review_text)
        msg += "📦 item: {0:.50}\n".format(item_title)
        msg += "👤 name: {0}\n".format(r['buyer']['buyerTitle'])
        try:
            country = COUNTRY_FLAGS[r['buyer']['buyerCountry']]
        except KeyError:
            country = "pirate_flag"

        msg += emoji.emojize(":{0}: {0}".format(country))

        await message.answer(msg)

    # result
    #     "resultList": [
    #       {
    #         "review": {
    #           "reviewId": 60088804112413800,
    #           "reviewDate": "25 фев 2025",
    #           "reviewContent": "Fits true. Nice material ",
    #           "reviewAdditional": null,
    #           "reviewStarts": 5,
    #           "reviewImages": null,
    #           "reviewAnonymous": false,
    #           "reviewHelpfulYes": 0,
    #           "reviewHelpfulNo": 0,
    #           "itemSpecInfo": "Color:Black Long Sleeve 3 Size:L ",
    #           "itemLogistics": "AliExpress Standard Shipping",
    #           "translation": {
    #             "reviewContent": "Подходит правда. Хороший материал",
    #             "reviewLanguage": "ru"
    #           }
    #         },
    #         "buyer": {
    #           "buyerTitle": "L***d",
    #           "buyerGender": null,
    #           "buyerCountry": "CA",
    #           "buyerImage": null
    #         }
    #       },
