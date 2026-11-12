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
from typing import Type

from core.menus.base_menu import BaseMenu, MenuTitleStyle
from core.types.color import Color


# noinspection DuplicatedCode
class KatapultFlashMethodHelpMenu(BaseMenu):
    def __init__(self, previous_menu: Type[BaseMenu] | None = None):
        super().__init__()
        self.title = "< ? > Help: Flash Katapult < ? >"
        self.title_color = Color.YELLOW
        self.title_style = MenuTitleStyle.PLAIN
        self.previous_menu: Type[BaseMenu] | None = previous_menu

    def set_previous_menu(self, previous_menu: Type[BaseMenu] | None) -> None:
        from components.katapult.menus.katapult_flash_menu import (
            KatapultFlashMethodMenu,
        )

        self.previous_menu = (
            previous_menu if previous_menu is not None else KatapultFlashMethodMenu
        )

    def set_options(self) -> None:
        pass

    def print_menu(self) -> None:
        subheader1 = Color.apply("Directly:", Color.CYAN)
        subheader2 = Color.apply("Update through Katapult:", Color.CYAN)
        subheader3 = Color.apply("Through another bootloader:", Color.CYAN)
        menu = textwrap.dedent(
            f"""
            ╟───────────────────────────────────────────────────────╢
            ║ {subheader1:<62} ║
            ║ Rebuilds Katapult with the selected config and writes ║
            ║ it with 'make flash'. Works for STM32 MCUs in DFU     ║
            ║ mode (using dfu-util) and RP2040/RP235x MCUs in boot  ║
            ║ mode. Both modes are usually entered by holding the   ║
            ║ BOOT button while powering up or resetting the board. ║
            ║ This erases Klipper, flash it again afterwards.       ║
            ║                                                       ║
            ║ {subheader2:<62} ║
            ║ For MCUs already running Katapult. Flashes the        ║
            ║ deployer with Katapult's flashtool, which replaces    ║
            ║ Katapult with the new build. Build the deployer with  ║
            ║ 'Build Katapult deployment application' set to the    ║
            ║ application offset of the installed Katapult.         ║
            ║                                                       ║
            ║ {subheader3:<62} ║
            ║ For MCUs with another bootloader, like the SD card    ║
            ║ bootloaders of many boards. The deployer is flashed   ║
            ║ with that bootloader and replaces it with Katapult.   ║
            ║ Build it with 'Build Katapult deployment application' ║
            ║ set to the offset of the existing bootloader.         ║
            ║                                                       ║
            ║ The deployer methods erase Klipper too. Rebuild it    ║
            ║ for Katapult's application offset and flash it again. ║
            ╟───────────────────────────────────────────────────────╢
            """
        )[1:]
        print(menu, end="")
