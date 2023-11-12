#!/usr/bin/env python

# ======================================================================= #
#  Copyright (C) 2020 - 2023 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #

import textwrap

from kiauh.core.menus.advanced_menu import AdvancedMenu
from kiauh.core.menus.base_menu import BaseMenu
from kiauh.core.menus.install_menu import InstallMenu
from kiauh.core.menus.remove_menu import RemoveMenu
from kiauh.core.menus.settings_menu import SettingsMenu
from kiauh.core.menus.update_menu import UpdateMenu
from kiauh.utils.constants import COLOR_MAGENTA, COLOR_CYAN, RESET_FORMAT


class MainMenu(BaseMenu):
    def __init__(self):
        super().__init__(
            header=True,
            options={
                0: self.test,
                1: InstallMenu,
                2: UpdateMenu,
                3: RemoveMenu,
                4: AdvancedMenu,
                5: None,
                6: SettingsMenu,
            },
            footer_type="quit",
        )

    def print_menu(self):
        menu = textwrap.dedent(
            f"""
            /=======================================================\\
            |     {COLOR_CYAN}~~~~~~~~~~~~~~~ [ Main Menu ] ~~~~~~~~~~~~~~~{RESET_FORMAT}     |
            |-------------------------------------------------------|
            |  0) [Log-Upload] |         Klipper: <TODO>            |
            |                  |            Repo: <TODO>            |
            |  1) [Install]    |                                    |
            |  2) [Update]     |       Moonraker: <TODO>            |
            |  3) [Remove]     |            Repo: <TODO>            |
            |  4) [Advanced]   |                                    |
            |  5) [Backup]     |        Mainsail: <TODO>            |
            |                  |          Fluidd: <TODO>            |
            |  6) [Settings]   |   KlipperScreen: <TODO>            |
            |                  |     Mobileraker: <TODO>            |
            |                  |                                    |
            |                  |       Crowsnest: <TODO>            |
            |                  |    Telegram Bot: <TODO>            |
            |                  |           Obico: <TODO>            |
            |                  |  OctoEverywhere: <TODO>            |
            |-------------------------------------------------------|
            |  {COLOR_CYAN}KIAUH v6.0.0{RESET_FORMAT}    |    Changelog: {COLOR_MAGENTA}https://git.io/JnmlX{RESET_FORMAT} |
            """
        )[1:]
        print(menu, end="")

    def test(self):
        print("blub")
