import io
import os.path
import urllib
from pathlib import Path
from typing import List, Optional
from urllib.parse import unquote, urlparse
from urllib.request import urlretrieve

from PIL import Image
from aiogram.types import FSInputFile, InputMediaPhoto

from src.core import config
from src.core.config import HERO, conf
from src.database import Favorite


# MEDIA HANDLERS ######################################################################
async def get_fs_input_hero_image(value: str) -> FSInputFile:
    """

    :param value:
    :return:
    """
    return FSInputFile(os.path.join(conf.static_path, HERO[value]))


async def get_input_media_hero_image(value: str, msg: str = None) -> InputMediaPhoto:
    """

    :param value:
    :param msg:
    :return:
    """
    return InputMediaPhoto(media=await get_fs_input_hero_image(value), caption=msg)


async def parse_url(url: str) -> str:
    """Парсит имя файла из url."""
    return unquote(Path(urlparse(url).path).name)


async def make_default_size_image(
    url: str,
) -> tuple[Optional[str], Optional[str]]:
    """
    Изменяет размер (1024х576) изображения товара и
    сохраняет в директории `static/products`
    """
    # try:
    file_name = await parse_url(url)
    full_path = os.path.join(config.IMAGE_PATH, file_name)

    fd = urllib.request.urlopen(url)
    input_img_file = io.BytesIO(fd.read())

    img = Image.open(input_img_file)
    img.thumbnail((config.THUMBNAIL, config.HEIGHT))
    img.save(fp=full_path, format=config.IMG_FORMAT)
    img_w, img_h = img.size

    bg = Image.new("RGB", (config.WIDTH, config.HEIGHT))
    bg_w, bg_h = bg.size
    offset = ((bg_w - img_w) // 2, (bg_h - img_h) // 2)
    bg.paste(im=img, box=offset)
    bg.save(fp=full_path, format=config.IMG_FORMAT, optimize=True, quality=25)

    bg.close()
    img.close()

    return full_path, file_name


# except Exception as error:
#     # todo add logger
#     return None, None


async def delete_img_from_static(obj: Favorite) -> bool:
    try:
        img_path = os.path.join(config.IMAGE_PATH, obj.image)
        if os.path.isfile(img_path):
            os.remove(img_path)
            return True
    except TypeError:
        return False


async def get_error_answer_photo(error: Exception) -> tuple[str, FSInputFile]:
    """

    :param error:
    :return:
    """
    photo = await get_fs_input_hero_image("error")
    msg = "⚠️ ОШИБКА\n{0}".format(error)
    return msg, photo


async def get_error_answer_media(error: Exception) -> InputMediaPhoto:
    """

    :param error:
    :return:
    """
    return await get_input_media_hero_image(
        "error", "⚠️ Произошла ошибка {0}".format(error)
    )


def separate_img_by_ten(images: List[str], num: int = 9) -> List[str]:
    """

    :param images:
    :param num:
    :return:
    """
    for i in range(0, len(images), num):
        yield list(images[i : i + num])
