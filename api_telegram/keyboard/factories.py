import json

from aiogram import types
from aiogram.utils import keyboard

from core import config


class KeysBuilder:
    def __init__(self, data: dict):
        for key, value in data.items():
            setattr(self, key, value)

    # def __getattr__(self, attr):
    #     return self[attr]

    def to_dict(self):
        return {key: value for (key, value) in self.__dict__.items()}

    def create_btn_callback_data(self, name, callback_data):
        return {getattr(self, name): callback_data}

    def create_btn_text(self, name):
        return {getattr(self, name): name}


# KEYBOARD BUILDER CLASS ###############################################
class KeyBoardBuilder:
    def __init__(self):
        self.kb = keyboard.InlineKeyboardBuilder()
        self.keys = KeysBuilder(config.KEYS).to_dict()
        self.factory = KeysBuilder(config.KEYS)

    def builder(
            self, data: list, size: tuple
    ) -> types.InlineKeyboardMarkup:
        """

        :param data:
        :param size:
        :return:
        """
        for data in data:
            for text, data in data.items():
                if isinstance(data, tuple):
                    button = types.InlineKeyboardButton(
                        text=text, url=data[1]
                    )
                else:
                    button = types.InlineKeyboardButton(
                        text=text, callback_data=data
                    )
                self.kb.add(button)
        return self.kb.adjust(*size).as_markup()

    def builder_url(
            self, data: list, size: tuple
    ) -> types.InlineKeyboardMarkup:
        """

        :param data:
        :param size:
        :return:
        """
        for data in data:
            for text, callback in data.items():
                button = types.InlineKeyboardButton(
                    text=text, url=callback
                )
                self.kb.add(button)
        return self.kb.adjust(*size).as_markup()

    def builder_id(
            self, prefix: str, uid: str, text: str, size: tuple
    ) -> types.InlineKeyboardMarkup:
        """

        :param prefix:
        :param uid:
        :param text:
        :param size:
        :return:
        """
        callback = "{0}_{1}".format(prefix, uid)
        button = types.InlineKeyboardButton(text=text, callback_data=callback)
        self.kb.add(button)
        return self.kb.adjust(*size).as_markup()


class KeyBoardFactory(KeyBoardBuilder):

    def __init__(self):
        super().__init__()
        self.keyboard_list = []
        self.markup = []

    def get_kb(self):
        return self.keyboard_list

    def get_markup(self):
        return tuple(self.markup)

    def add_button_first(self, obj):
        self.keyboard_list.insert(0, obj)
        return self

    def add_button(self, obj):
        self.keyboard_list.append(obj)
        return self

    def add_buttons(self, objs: list):
        self.keyboard_list.extend(objs)
        return self

    def add_markup(self, obj):
        self.markup.append(obj)
        return self

    def update_markup(self, obj):
        self.markup.pop()
        self.add_markup(obj)
        return self

    def add_markups(self, objs: list):
        self.markup.extend(objs)
        return self

    def add_markup_first(self, obj):
        self.markup.insert(0, obj)
        return self

    def create_kb(self):
        return self.builder(
            self.get_kb(),
            self.get_markup()
        )


class BasePaginationBtn(KeyBoardFactory):
    def __init__(self):
        super().__init__()

    def btn_text(self, name):
        return self.factory.create_btn_text(name)

    def btn_data(self, name, data):
        return self.factory.create_btn_callback_data(name, data)
