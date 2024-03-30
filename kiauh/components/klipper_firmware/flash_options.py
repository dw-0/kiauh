# ======================================================================= #
#  Copyright (C) 2020 - 2024 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #

from dataclasses import field, dataclass
from enum import Enum
from typing import Union, List


class FlashMethod(Enum):
    REGULAR = "REGULAR"
    SD_CARD = "SD_CARD"


class FlashCommand(Enum):
    FLASH = "flash"
    SERIAL_FLASH = "serialflash"


class ConnectionType(Enum):
    USB = "USB"
    USB_DFU = "USB_DFU"
    UART = "UART"


@dataclass
class FlashOptions:
    _instance = None
    flash_method: Union[FlashMethod, None] = None
    flash_command: Union[FlashCommand, None] = None
    connection_type: Union[ConnectionType, None] = None
    mcu_list: List[str] = field(default_factory=list)
    selected_mcu: str = ""
    selected_board: str = ""

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(FlashOptions, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    @classmethod
    def destroy(cls):
        cls._instance = None
