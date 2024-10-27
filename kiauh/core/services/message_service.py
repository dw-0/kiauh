# ======================================================================= #
#  Copyright (C) 2020 - 2024 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #

from dataclasses import dataclass, field
from typing import List

from core.logger import DialogType, Logger
from core.types.color import Color


@dataclass()
class Message:
    title: str = field(default="")
    text: List[str] = field(default_factory=list)
    color: Color = field(default=Color.WHITE)
    centered: bool = field(default=False)


class MessageService:
    _instance = None

    def __new__(cls) -> "MessageService":
        if cls._instance is None:
            cls._instance = super(MessageService, cls).__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        if not hasattr(self, "__initialized"):
            self.__initialized = False
        if self.__initialized:
            return
        self.__initialized = True
        self.message = None

    def set_message(self, message: Message) -> None:
        self.message = message

    def display_message(self) -> None:
        if self.message is None:
            return

        Logger.print_dialog(
            title=DialogType.CUSTOM,
            content=self.message.text,
            custom_title=self.message.title,
            custom_color=self.message.color,
            center_content=self.message.centered,
        )

        self.__clear_message()

    def __clear_message(self) -> None:
        self.message = None
