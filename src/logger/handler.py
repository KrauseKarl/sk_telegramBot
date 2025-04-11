import logging as lg
import os
from pathlib import Path
from typing import Dict

from src.core.config import LOGGER_PATH


class LevelFileHandler(lg.Handler):
    """
    Кастомный класс logging-handler.

    Принимает два параметра:
    mode - режим записи в файл,
    levels_dict - словарь,
    где ключ это имя уровня логирования,
    а значение - путь до лог-файла для записи
    определенного уровня.
    """

    LEVELS = {
        "info": os.path.join(LOGGER_PATH, "info.log"),
        "error": os.path.join(LOGGER_PATH, "error.log"),
    }

    def __init__(self, levels_dict: Dict[str, str] | None, mode: str = "a") -> None:
        super().__init__()
        self.mode = mode
        self.levels_dict = levels_dict if levels_dict else self.LEVELS

    def emit(self, record: lg.LogRecord) -> None:
        message = self.format(record)
        level = record.levelname
        # self.get_or_create_logfile(level)
        self.record_message(level, message)

    def record_message(self, level: str, message: str) -> None:
        """Делает запись в лог-файл."""
        with open(self.get_or_set_path(level), mode=self.mode) as file_log:
            file_log.write(message + "\n")  # noqa: WPS336

    def get_or_create_logfile(self, level: str) -> None:  # noqa: WPS463
        """Функция создает лог-файл в зависимости от уровня логирования."""
        abspath_log = Path(__file__).resolve(strict=True).parent
        abspath_logger = os.path.join(abspath_log, self.levels_dict[level])
        if not os.path.exists(abspath_logger):
            # file = open(self.get_or_set_path(level), mode=self.mode).close()
            with open(abspath_logger, mode=self.mode) as file_log:
                file_log.write(f" [LOG LEVEL {level}]\n\n")

    def get_or_set_path(self, level: str) -> str:
        """Функция возвращает путь до лог-файла."""
        base_dir = os.path.dirname(os.path.abspath(__file__))
        if level.lower() in self.levels_dict.keys():
            log_path = self.levels_dict[level.lower()]
        else:
            log_path = self.levels_dict["debug"]

        return os.path.join(base_dir, log_path)
