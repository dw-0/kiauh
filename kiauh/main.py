#!/usr/bin/env python3

# ======================================================================= #
#  Copyright (C) 2020 - 2024 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #

from kiauh.core.menus.main_menu import MainMenu
from kiauh.utils.logger import Logger


def main():
    try:
        MainMenu().start()
    except KeyboardInterrupt:
        Logger.print_ok("\nHappy printing!\n", prefix=False)
