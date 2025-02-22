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

from components.klipper_firmware.flash_options import FlashMethod, FlashOptions
from core.menus import FooterType, Option
from core.menus.base_menu import BaseMenu, MenuTitleStyle
from core.types.color import Color


# noinspection PyUnusedLocal
# noinspection PyMethodMayBeStatic
class KlipperNoFirmwareErrorMenu(BaseMenu):
    def __init__(self, previous_menu: Type[BaseMenu] | None = None):
        super().__init__()
        self.title = "!!! NO FIRMWARE FILE FOUND !!!"
        self.title_color = Color.RED
        self.title_style = MenuTitleStyle.PLAIN
        self.previous_menu: Type[BaseMenu] | None = previous_menu

        self.flash_options = FlashOptions()
        self.footer_type = FooterType.BLANK
        self.input_label_txt = "Press ENTER to go back to [Advanced Menu]"

    def set_previous_menu(self, previous_menu: Type[BaseMenu] | None) -> None:
        self.previous_menu = previous_menu

    def set_options(self) -> None:
        self.default_option = Option(method=self.go_back)

    def print_menu(self) -> None:
        line1 = "Unable to find a compiled firmware file!"
        menu = textwrap.dedent(
            f"""
            ╟───────────────────────────────────────────────────────╢
            ║ {Color.apply(line1, Color.RED):<62} ║
            ║                                                       ║
            ║ Make sure, that:                                      ║
            ║ ● the folder '~/klipper/out' and its content exist    ║
            ║ ● the folder contains the following file:             ║
            """
        )[1:]

        if self.flash_options.flash_method is FlashMethod.REGULAR:
            menu += "║   ● 'klipper.elf'                                     ║\n"
            menu += "║   ● 'klipper.elf.hex'                                 ║\n"
        else:
            menu += "║   ● 'klipper.bin'                                     ║\n"

        print(menu, end="")

    def go_back(self, **kwargs) -> None:
        from core.menus.advanced_menu import AdvancedMenu

        AdvancedMenu().run()


# noinspection PyUnusedLocal
# noinspection PyMethodMayBeStatic
class KlipperNoBoardTypesErrorMenu(BaseMenu):
    def __init__(self, previous_menu: Type[BaseMenu] | None = None):
        super().__init__()
        self.title = "!!! ERROR GETTING BOARD LIST !!!"
        self.title_color = Color.RED
        self.title_style = MenuTitleStyle.PLAIN
        self.previous_menu: Type[BaseMenu] | None = previous_menu
        self.footer_type = FooterType.BLANK
        self.input_label_txt = "Press ENTER to go back to [Main Menu]"

    def set_previous_menu(self, previous_menu: Type[BaseMenu] | None) -> None:
        self.previous_menu = previous_menu

    def set_options(self) -> None:
        self.default_option = Option(method=self.go_back)

    def print_menu(self) -> None:
        line1 = "Reading the list of supported boards failed!"
        menu = textwrap.dedent(
            f"""
            ╟───────────────────────────────────────────────────────╢
            ║ {Color.apply(line1, Color.RED):<62} ║
            ║                                                       ║
            ║ Make sure, that:                                      ║
            ║ ● the folder '~/klipper' and all its content exist    ║
            ║ ● the content of folder '~/klipper' is not currupted  ║
            ║ ● the file '~/klipper/scripts/flash-sd.py' exist      ║
            ║ ● your current user has access to those files/folders ║
            ║                                                       ║
            ║ If in doubt or this process continues to fail, please ║
            ║ consider to download Klipper again.                   ║
            """
        )[1:]
        print(menu, end="")

    def go_back(self, **kwargs) -> None:
        from core.menus.main_menu import MainMenu

        MainMenu().run()
