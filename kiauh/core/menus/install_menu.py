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
from kiauh.modules.klipper import klipper_setup
from kiauh.utils.constants import COLOR_GREEN, RESET_FORMAT


# noinspection PyMethodMayBeStatic
class InstallMenu(BaseMenu):
    def __init__(self):
        super().__init__(
            header=True,
            options={
                1: self.install_klipper,
                2: self.install_moonraker,
                3: self.install_mainsail,
                4: self.install_fluidd,
                5: self.install_klipperscreen,
                6: self.install_pretty_gcode,
                7: self.install_telegram_bot,
                8: self.install_obico,
                9: self.install_octoeverywhere,
                10: self.install_mobileraker,
                11: self.install_crowsnest,
            },
            footer_type=BACK_FOOTER,
        )

    def print_menu(self):
        header = " [ Installation Menu ] "
        color = COLOR_GREEN
        count = 62 - len(color) - len(RESET_FORMAT)
        menu = textwrap.dedent(
            f"""
            /=======================================================\\
            | {color}{header:~^{count}}{RESET_FORMAT} |
            |-------------------------------------------------------|
            | Firmware & API:          | Other:                     |
            |  1) [Klipper]            |  6) [PrettyGCode]          |
            |  2) [Moonraker]          |  7) [Telegram Bot]         |
            |                          |  8) $(obico_install_title) |
            | Klipper Webinterface:    |  9) [OctoEverywhere]       |
            |  3) [Mainsail]           | 10) [Mobileraker]          |
            |  4) [Fluidd]             |                            |
            |                          | Webcam Streamer:           |
            | Touchscreen GUI:         | 11) [Crowsnest]            |
            |  5) [KlipperScreen]      |                            |
            """
        )[1:]
        print(menu, end="")

    def install_klipper(self):
        klipper_setup.run_klipper_setup(install=True)

    def install_moonraker(self):
        print("install_moonraker")

    def install_mainsail(self):
        print("install_mainsail")

    def install_fluidd(self):
        print("install_fluidd")

    def install_klipperscreen(self):
        print("install_klipperscreen")

    def install_pretty_gcode(self):
        print("install_pretty_gcode")

    def install_telegram_bot(self):
        print("install_telegram_bot")

    def install_obico(self):
        print("install_obico")

    def install_octoeverywhere(self):
        print("install_octoeverywhere")

    def install_mobileraker(self):
        print("install_mobileraker")

    def install_crowsnest(self):
        print("install_crowsnest")
