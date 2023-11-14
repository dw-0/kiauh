#!/usr/bin/env python3

# ======================================================================= #
#  Copyright (C) 2020 - 2023 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #

import textwrap

from kiauh.core.menus import BACK_FOOTER
from kiauh.core.menus.base_menu import BaseMenu
from kiauh.utils.constants import COLOR_YELLOW, RESET_FORMAT


class AdvancedMenu(BaseMenu):
    def __init__(self):
        super().__init__(header=True, options={}, footer_type=BACK_FOOTER)

    def print_menu(self):
        header = " [ Advanced Menu ] "
        color = COLOR_YELLOW
        count = 62 - len(color) - len(RESET_FORMAT)
        menu = textwrap.dedent(
            f"""
            /=======================================================\\
            | {color}{header:~^{count}}{RESET_FORMAT} |
            |-------------------------------------------------------|
            | Klipper & API:          | Mainsail:                   |
            |  0) [Rollback]          |  5) [Theme installer]       |
            |                         |                             |
            | Firmware:               | System:                     |
            |  1) [Build only]        |  6) [Change hostname]       |
            |  2) [Flash only]        |                             |
            |  3) [Build + Flash]     | Extras:                     |
            |  4) [Get MCU ID]        |  7) [G-Code Shell Command]  |
            """
        )[1:]
        print(menu, end="")
