# ======================================================================= #
#  Copyright (C) 2020 - 2024 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #

import textwrap

from components.klipper_firmware.menus.klipper_flash_menu import KlipperFlashMethodMenu
from core.menus import BACK_FOOTER
from core.menus.base_menu import BaseMenu
from utils.constants import COLOR_YELLOW, RESET_FORMAT


class AdvancedMenu(BaseMenu):
    def __init__(self):
        super().__init__(
            header=True,
            options={
                "1": None,
                "2": None,
                "3": None,
                "4": KlipperFlashMethodMenu,
                "5": None,
                "6": None,
            },
            footer_type=BACK_FOOTER,
        )

    def print_menu(self):
        header = " [ Advanced Menu ] "
        color = COLOR_YELLOW
        count = 62 - len(color) - len(RESET_FORMAT)
        menu = textwrap.dedent(
            f"""
            /=======================================================\\
            | {color}{header:~^{count}}{RESET_FORMAT} |
            |-------------------------------------------------------|
            | Repo Rollback:                                        |
            |  1) [Klipper]                                         |
            |  2) [Moonraker]                                       |
            |                                                       |
            | Klipper Firmware:                                     |
            |  3) [Build]                                           |
            |  4) [Flash]                                           |
            |  5) [Build + Flash]                                   |
            |  6) [Get MCU ID]                                      |   
            """
        )[1:]
        print(menu, end="")
