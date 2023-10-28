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
from kiauh.modules.klipper import klipper_setup
from kiauh.utils.constants import COLOR_RED, RESET_FORMAT


# noinspection PyMethodMayBeStatic
class RemoveMenu(BaseMenu):
    def __init__(self):
        super().__init__(
            header=True,
            options={
                1: self.remove_klipper,
                2: self.remove_moonraker,
                3: self.remove_mainsail,
                4: self.remove_mainsail_config,
                5: self.remove_fluidd,
                6: self.remove_fluidd_config,
                7: self.remove_klipperscreen,
                8: self.remove_crowsnest,
                9: self.remove_mjpgstreamer,
                10: self.remove_pretty_gcode,
                11: self.remove_telegram_bot,
                12: self.remove_obico,
                13: self.remove_octoeverywhere,
                14: self.remove_mobileraker,
                15: self.remove_nginx,
            },
            footer_type="back",
        )

    def print_menu(self):
        menu = textwrap.dedent(
            f"""
            /=======================================================\\
            |     {COLOR_RED}~~~~~~~~~~~~~~ [ Remove Menu ] ~~~~~~~~~~~~~~{RESET_FORMAT}     |
            |-------------------------------------------------------|
            | INFO: Configurations and/or any backups will be kept! |
            |-------------------------------------------------------|
            | Firmware & API:           | Webcam Streamer:          |
            |  1) [Klipper]             |  8) [Crowsnest]           |
            |  2) [Moonraker]           |  9) [MJPG-Streamer]       |
            |                           |                           |
            | Klipper Webinterface:     | Other:                    |
            |  3) [Mainsail]            | 10) [PrettyGCode]         |
            |  4) [Mainsail-Config]     | 11) [Telegram Bot]        |
            |  5) [Fluidd]              | 12) [Obico for Klipper]   |
            |  6) [Fluidd-Config]       | 13) [OctoEverywhere]      |
            |                           | 14) [Mobileraker]         |
            | Touchscreen GUI:          | 15) [NGINX]               |
            |  7) [KlipperScreen]       |                           |
            """
        )[1:]
        print(menu, end="")

    def remove_klipper(self):
        klipper_setup.run_klipper_setup(install=False)

    def remove_moonraker(self):
        print("remove_moonraker")

    def remove_mainsail(self):
        print("remove_mainsail")

    def remove_mainsail_config(self):
        print("remove_mainsail_config")

    def remove_fluidd(self):
        print("remove_fluidd")

    def remove_fluidd_config(self):
        print("remove_fluidd_config")

    def remove_klipperscreen(self):
        print("remove_klipperscreen")

    def remove_crowsnest(self):
        print("remove_crowsnest")

    def remove_mjpgstreamer(self):
        print("remove_mjpgstreamer")

    def remove_pretty_gcode(self):
        print("remove_pretty_gcode")

    def remove_telegram_bot(self):
        print("remove_telegram_bot")

    def remove_obico(self):
        print("remove_obico")

    def remove_octoeverywhere(self):
        print("remove_octoeverywhere")

    def remove_mobileraker(self):
        print("remove_mobileraker")

    def remove_nginx(self):
        print("remove_nginx")
