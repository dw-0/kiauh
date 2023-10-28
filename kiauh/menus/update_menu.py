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

from kiauh.menus.base_menu import BaseMenu
from kiauh.utils.constants import COLOR_GREEN, RESET_FORMAT


# noinspection PyMethodMayBeStatic
class UpdateMenu(BaseMenu):
    def __init__(self):
        super().__init__(
            header=True,
            options={
                0: self.update_all,
                1: self.update_klipper,
                2: self.update_moonraker,
                3: self.update_mainsail,
                4: self.update_fluidd,
                5: self.update_klipperscreen,
                6: self.update_pgc_for_klipper,
                7: self.update_telegram_bot,
                8: self.update_moonraker_obico,
                9: self.update_octoeverywhere,
                10: self.update_mobileraker,
                11: self.update_crowsnest,
                12: self.upgrade_system_packages,
            },
            footer_type="back",
        )

    def print_menu(self):
        menu = textwrap.dedent(
            f"""
            /=======================================================\\
            |     {COLOR_GREEN}~~~~~~~~~~~~~~ [ Update Menu ] ~~~~~~~~~~~~~~{RESET_FORMAT}     |
            |-------------------------------------------------------|
            |  0) [Update all]        |              |              |
            |                         | Current:     | Latest:      |
            | Klipper & API:          |--------------|--------------|
            |  1) [Klipper]           |              |              |
            |  2) [Moonraker]         |              |              |
            |                         |              |              |
            | Klipper Webinterface:   |--------------|--------------|
            |  3) [Mainsail]          |              |              |
            |  4) [Fluidd]            |              |              |
            |                         |              |              |
            | Touchscreen GUI:        |--------------|--------------|
            |  5) [KlipperScreen]     |              |              |
            |                         |              |              |
            | Other:                  |--------------|--------------|
            |  6) [PrettyGCode]       |              |              |
            |  7) [Telegram Bot]      |              |              |
            |  8) [Obico for Klipper] |              |              |
            |  9) [OctoEverywhere]    |              |              |
            | 10) [Mobileraker]       |              |              |
            | 11) [Crowsnest]         |              |              |
            |                         |-----------------------------|
            | 12) [System]            |              |              |
            """
        )[1:]
        print(menu, end="")

    def update_all(self):
        print("update_all")

    def update_klipper(self):
        print("update_klipper")

    def update_moonraker(self):
        print("update_moonraker")

    def update_mainsail(self):
        print("update_mainsail")

    def update_fluidd(self):
        print("update_fluidd")

    def update_klipperscreen(self):
        print("update_klipperscreen")

    def update_pgc_for_klipper(self):
        print("update_pgc_for_klipper")

    def update_telegram_bot(self):
        print("update_telegram_bot")

    def update_moonraker_obico(self):
        print("update_moonraker_obico")

    def update_octoeverywhere(self):
        print("update_octoeverywhere")

    def update_mobileraker(self):
        print("update_mobileraker")

    def update_crowsnest(self):
        print("update_crowsnest")

    def upgrade_system_packages(self):
        print("upgrade_system_packages")
