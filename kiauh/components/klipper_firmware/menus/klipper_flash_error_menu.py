# ======================================================================= #
#  Copyright (C) 2020 - 2024 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #
import textwrap

from components.klipper_firmware.flash_options import FlashOptions, FlashMethod
from core.menus import FooterType
from core.menus.base_menu import BaseMenu
from utils.constants import COLOR_RED, RESET_FORMAT


# noinspection PyUnusedLocal
# noinspection PyMethodMayBeStatic
class KlipperNoFirmwareErrorMenu(BaseMenu):
    def __init__(self):
        super().__init__()

        self.flash_options = FlashOptions()
        self.default_option = self.go_back
        self.footer_type = FooterType.BLANK
        self.input_label_txt = "Press ENTER to go back to [Advanced Menu]"

    def print_menu(self) -> None:
        header = "!!! NO FIRMWARE FILE FOUND !!!"
        color = COLOR_RED
        count = 62 - len(color) - len(RESET_FORMAT)
        line1 = f"{color}Unable to find a compiled firmware file!{RESET_FORMAT}"
        menu = textwrap.dedent(
            f"""
            /=======================================================\\
            | {color}{header:^{count}}{RESET_FORMAT} |
            |-------------------------------------------------------|
            | {line1:<62} |
            |                                                       |
            | Make sure, that:                                      |
            | ● the folder '~/klipper/out' and its content exist    |
            | ● the folder contains the following file:             |
            """
        )[1:]

        if self.flash_options.flash_method is FlashMethod.REGULAR:
            menu += "|   ● 'klipper.elf'                                     |\n"
            menu += "|   ● 'klipper.elf.hex'                                 |\n"
        else:
            menu += "|   ● 'klipper.bin'                                     |\n"

        print(menu, end="")

    def go_back(self, **kwargs) -> None:
        from core.menus.advanced_menu import AdvancedMenu

        AdvancedMenu().run()


# noinspection PyUnusedLocal
# noinspection PyMethodMayBeStatic
class KlipperNoBoardTypesErrorMenu(BaseMenu):
    def __init__(self):
        super().__init__()

        self.default_option = self.go_back
        self.footer_type = FooterType.BLANK
        self.input_label_txt = "Press ENTER to go back to [Main Menu]"

    def print_menu(self) -> None:
        header = "!!! ERROR GETTING BOARD LIST !!!"
        color = COLOR_RED
        count = 62 - len(color) - len(RESET_FORMAT)
        line1 = f"{color}Reading the list of supported boards failed!{RESET_FORMAT}"
        menu = textwrap.dedent(
            f"""
            /=======================================================\\
            | {color}{header:^{count}}{RESET_FORMAT} |
            |-------------------------------------------------------|
            | {line1:<62} |
            |                                                       |
            | Make sure, that:                                      |
            | ● the folder '~/klipper' and all its content exist    |
            | ● the content of folder '~/klipper' is not currupted  |
            | ● the file '~/klipper/scripts/flash-sd.py' exist      |
            | ● your current user has access to those files/folders |
            |                                                       |
            | If in doubt or this process continues to fail, please |
            | consider to download Klipper again.                   |
            """
        )[1:]
        print(menu, end="")

    def go_back(self, **kwargs) -> None:
        from core.menus.main_menu import MainMenu

        MainMenu().run()