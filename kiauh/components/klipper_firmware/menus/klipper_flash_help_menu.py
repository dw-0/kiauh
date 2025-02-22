# ======================================================================= #
#  Copyright (C) 2020 - 2025 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #
from __future__ import annotations

import textwrap
from typing import Tuple, Type

from core.menus.base_menu import BaseMenu, MenuTitleStyle
from core.types.color import Color


def __title_config__() -> Tuple[str, Color, MenuTitleStyle]:
    return "< ? > Help: Flash MCU < ? >", Color.YELLOW, MenuTitleStyle.PLAIN


# noinspection DuplicatedCode
class KlipperFlashMethodHelpMenu(BaseMenu):
    def __init__(self, previous_menu: Type[BaseMenu] | None = None):
        super().__init__()
        self.title, self.title_color, self.title_style = __title_config__()
        self.previous_menu: Type[BaseMenu] | None = previous_menu

    def set_previous_menu(self, previous_menu: Type[BaseMenu] | None) -> None:
        from components.klipper_firmware.menus.klipper_flash_menu import (
            KlipperFlashMethodMenu,
        )

        self.previous_menu = (
            previous_menu if previous_menu is not None else KlipperFlashMethodMenu
        )

    def set_options(self) -> None:
        pass

    def print_menu(self) -> None:
        subheader1 = Color.apply("Regular flashing method:", Color.CYAN)
        subheader2 = Color.apply("Updating via SD-Card Update:", Color.CYAN)
        menu = textwrap.dedent(
            f"""
            ╟───────────────────────────────────────────────────────╢
            ║ {subheader1:<62} ║
            ║ The default method to flash controller boards which   ║
            ║ are connected and updated over USB and not by placing ║
            ║ a compiled firmware file onto an internal SD-Card.    ║
            ║                                                       ║
            ║ Common controllers that get flashed that way are:     ║
            ║ - Arduino Mega 2560                                   ║
            ║ - Fysetc F6 / S6 (used without a Display + SD-Slot)   ║
            ║                                                       ║
            ║ {subheader2:<62} ║
            ║ Many popular controller boards ship with a bootloader ║
            ║ capable of updating the firmware via SD-Card.         ║
            ║ Choose this method if your controller board supports  ║
            ║ this way of updating. This method ONLY works for up-  ║
            ║ grading firmware. The initial flashing procedure must ║
            ║ be done manually per the instructions that apply to   ║
            ║ your controller board.                                ║
            ║                                                       ║
            ║ Common controllers that can be flashed that way are:  ║
            ║ - BigTreeTech SKR 1.3 / 1.4 (Turbo) / E3 / Mini E3    ║
            ║ - Fysetc F6 / S6 (used with a Display + SD-Slot)      ║
            ║ - Fysetc Spider                                       ║
            ║                                                       ║
            ╟───────────────────────────────────────────────────────╢
            """
        )[1:]
        print(menu, end="")


# noinspection DuplicatedCode
class KlipperFlashCommandHelpMenu(BaseMenu):
    def __init__(self, previous_menu: Type[BaseMenu] | None = None):
        super().__init__()
        self.title, self.title_color, self.title_style = __title_config__()
        self.previous_menu: Type[BaseMenu] | None = previous_menu

    def set_previous_menu(self, previous_menu: Type[BaseMenu] | None) -> None:
        from components.klipper_firmware.menus.klipper_flash_menu import (
            KlipperFlashCommandMenu,
        )

        self.previous_menu = (
            previous_menu if previous_menu is not None else KlipperFlashCommandMenu
        )

    def set_options(self) -> None:
        pass

    def print_menu(self) -> None:
        subheader1 = Color.apply("make flash:", Color.CYAN)
        subheader2 = Color.apply("make serialflash:", Color.CYAN)
        menu = textwrap.dedent(
            f"""
            ╟───────────────────────────────────────────────────────╢
            ║ {subheader1:<62} ║
            ║ The default command to flash controller board, it     ║
            ║ will detect selected microcontroller and use suitable ║
            ║ tool for flashing it.                                 ║
            ║                                                       ║
            ║ {subheader2:<62} ║
            ║ Special command to flash STM32 microcontrollers in    ║
            ║ DFU mode but connected via serial. stm32flash command ║
            ║ will be used internally.                              ║
            ║                                                       ║
            """
        )[1:]
        print(menu, end="")


# noinspection DuplicatedCode
class KlipperMcuConnectionHelpMenu(BaseMenu):
    def __init__(self, previous_menu: Type[BaseMenu] | None = None):
        super().__init__()
        self.title, self.title_color, self.title_style = __title_config__()
        self.previous_menu: Type[BaseMenu] | None = previous_menu

    def set_previous_menu(self, previous_menu: Type[BaseMenu] | None) -> None:
        from components.klipper_firmware.menus.klipper_flash_menu import (
            KlipperSelectMcuConnectionMenu,
        )

        self.previous_menu = (
            previous_menu
            if previous_menu is not None
            else KlipperSelectMcuConnectionMenu
        )

    def set_options(self) -> None:
        pass

    def print_menu(self) -> None:
        subheader1 = Color.apply("USB:", Color.CYAN)
        subheader2 = Color.apply("UART:", Color.CYAN)
        subheader3 = Color.apply("USB DFU:", Color.CYAN)
        subheader4 = Color.apply("USB RP2040 Boot:", Color.CYAN)
        menu = textwrap.dedent(
            f"""
            ╟───────────────────────────────────────────────────────╢
            ║ {subheader1:<62} ║
            ║ Selecting USB as the connection method will scan the  ║
            ║ USB ports for connected controller boards. This will  ║
            ║ be similar to the 'ls /dev/serial/by-id/*' command    ║
            ║ suggested by the official Klipper documentation for   ║
            ║ determining successfull USB connections!              ║
            ║                                                       ║
            ║ {subheader2:<62} ║
            ║ Selecting UART as the connection method will list all ║
            ║ possible UART serial ports. Note: This method ALWAYS  ║
            ║ returns something as it seems impossible to determine ║
            ║ if a valid Klipper controller board is connected or   ║
            ║ not. Because of that, you MUST know which UART serial ║
            ║ port your controller board is connected to when using ║
            ║ this connection method.                               ║
            ║                                                       ║
            ║ {subheader3:<62} ║
            ║ Selecting USB DFU as the connection method will scan  ║
            ║ the USB ports for connected controller boards in      ║
            ║ STM32 DFU mode, which is usually done by holding down ║
            ║ the BOOT button or setting a special jumper on the    ║
            ║ board before powering up.                             ║
            ║                                                       ║
            ║ {subheader4:<62} ║
            ║ Selecting USB RP2 Boot as the connection method will  ║
            ║ scan the USB ports for connected RP2040 controller    ║
            ║ boards in Boot mode, which is usually done by holding ║
            ║ down the BOOT button before powering up.              ║
            ║                                                       ║
            ╟───────────────────────────────────────────────────────╢
            """
        )[1:]
        print(menu, end="")
