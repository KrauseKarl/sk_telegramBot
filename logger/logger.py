import logging as lg
import os
import sys
from typing import Dict

from core.config import BASE_DIR
from logger.handler import LevelFileHandler


def set_logger_files() -> None:
    """Функция создает папку с лог-файлами (`debug`,`info`,`error`)."""
    for level, path in LevelFileHandler.LEVELS.items():
        logger_folder_path = os.path.join(
            BASE_DIR, "logger"
        )
        if not os.path.exists(logger_folder_path):
            os.mkdir(logger_folder_path)

        logger_file_path = os.path.join(BASE_DIR, "logger", path)
        if not os.path.exists(logger_file_path):
            with open(logger_file_path, mode="w") as f:
                f.write(f"logger level [{level.upper()}]\n")


def get_logger(name: str, levels: Dict[str, str] | None = None) -> lg.Logger:
    """
    Функция по созданию экземпляры класса Logger.

    :param name: Название логгера,
    :param levels: Словарь с уровнями логирования и названиями файлов.
    :return: Logger.
    """
    lg.basicConfig(
        level=lg.INFO,
        stream=sys.stdout,
    )

    log = lg.getLogger(name)
    handlers = LevelFileHandler(levels)
    formatter = lg.Formatter(
        fmt="%(levelname)s %(asctime)s [%(funcName)s:%(lineno)d] %(message)s",  # noqa: WPS323, E501
        datefmt="%Y-%m-%d,%H:%M:%S",  # noqa: WPS323
    )
    handlers.setFormatter(formatter)
    log.addHandler(handlers)
    log.propagate = False
    return log


info_log = get_logger("info")
error_log = get_logger("error")
