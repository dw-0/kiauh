# ======================================================================= #
#  Copyright (C) 2020 - 2025 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #
from __future__ import annotations

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
    __cls_instance = None
    __message: Message | None

    def __new__(cls) -> "MessageService":
        if cls.__cls_instance is None:
            cls.__cls_instance = super(MessageService, cls).__new__(cls)
        return cls.__cls_instance

    def __init__(self) -> None:
        if not hasattr(self, "__initialized"):
            self.__initialized = False
        if self.__initialized:
            return
        self.__initialized = True
        self.__message = None

    def set_message(self, message: Message) -> None:
        self.__message = message

    def display_message(self) -> None:
        if self.__message is None:
            return

        Logger.print_dialog(
            title=DialogType.CUSTOM,
            content=self.__message.text,
            custom_title=self.__message.title,
            custom_color=self.__message.color,
            center_content=self.__message.centered,
        )

        self.__clear_message()

    def __clear_message(self) -> None:
        self.__message = None
