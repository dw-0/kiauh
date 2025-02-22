# ======================================================================= #
#  Copyright (C) 2020 - 2025 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #
from __future__ import annotations

from dataclasses import field
from enum import Enum
from typing import List


class FlashMethod(Enum):
    REGULAR = "Regular"
    SD_CARD = "SD Card"


class FlashCommand(Enum):
    FLASH = "flash"
    SERIAL_FLASH = "serialflash"


class ConnectionType(Enum):
    USB = "USB"
    USB_DFU = "USB (DFU)"
    USB_RP2040 = "USB (RP2040)"
    UART = "UART"


class FlashOptions:
    _instance = None
    _flash_method: FlashMethod | None = None
    _flash_command: FlashCommand | None = None
    _connection_type: ConnectionType | None = None
    _mcu_list: List[str] = field(default_factory=list)
    _selected_mcu: str = ""
    _selected_board: str = ""
    _selected_baudrate: int = 250000
    _selected_kconfig: str = ".config"

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(FlashOptions, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    @classmethod
    def destroy(cls) -> None:
        cls._instance = None

    @property
    def flash_method(self) -> FlashMethod | None:
        return self._flash_method

    @flash_method.setter
    def flash_method(self, value: FlashMethod | None):
        self._flash_method = value

    @property
    def flash_command(self) -> FlashCommand | None:
        return self._flash_command

    @flash_command.setter
    def flash_command(self, value: FlashCommand | None):
        self._flash_command = value

    @property
    def connection_type(self) -> ConnectionType | None:
        return self._connection_type

    @connection_type.setter
    def connection_type(self, value: ConnectionType | None):
        self._connection_type = value

    @property
    def mcu_list(self) -> List[str]:
        return self._mcu_list

    @mcu_list.setter
    def mcu_list(self, value: List[str]) -> None:
        self._mcu_list = value

    @property
    def selected_mcu(self) -> str:
        return self._selected_mcu

    @selected_mcu.setter
    def selected_mcu(self, value: str) -> None:
        self._selected_mcu = value

    @property
    def selected_board(self) -> str:
        return self._selected_board

    @selected_board.setter
    def selected_board(self, value: str) -> None:
        self._selected_board = value

    @property
    def selected_baudrate(self) -> int:
        return self._selected_baudrate

    @selected_baudrate.setter
    def selected_baudrate(self, value: int) -> None:
        self._selected_baudrate = value

    @property
    def selected_kconfig(self) -> str:
        return self._selected_kconfig

    @selected_kconfig.setter
    def selected_kconfig(self, value: str) -> None:
        self._selected_kconfig = value
