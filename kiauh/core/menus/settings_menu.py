#!/usr/bin/env python3

# ======================================================================= #
#  Copyright (C) 2020 - 2023 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #

from kiauh.core.menus.base_menu import BaseMenu


# noinspection PyMethodMayBeStatic
class SettingsMenu(BaseMenu):
    def __init__(self):
        super().__init__(header=True, options={})

    def print_menu(self):
        print("self")

    def execute_option_p(self):
        # Implement the functionality for Option P
        print("Executing Option P")

    def execute_option_q(self):
        # Implement the functionality for Option Q
        print("Executing Option Q")

    def execute_option_r(self):
        # Implement the functionality for Option R
        print("Executing Option R")
