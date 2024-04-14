# ======================================================================= #
#  Copyright (C) 2020 - 2024 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #
from typing import Type, Optional

from core.menus.base_menu import BaseMenu


# noinspection PyMethodMayBeStatic
class SettingsMenu(BaseMenu):
    def __init__(self):
        super().__init__()

    def set_previous_menu(self, previous_menu: Optional[Type[BaseMenu]]) -> None:
        from core.menus.main_menu import MainMenu

        self.previous_menu: Type[BaseMenu] = (
            previous_menu if previous_menu is not None else MainMenu
        )

    def set_options(self) -> None:
        pass

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
