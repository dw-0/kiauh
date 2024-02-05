#!/usr/bin/env python3

# ======================================================================= #
#  Copyright (C) 2020 - 2024 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #

import textwrap

from kiauh.core.menus import BACK_FOOTER
from kiauh.core.menus.base_menu import BaseMenu
from kiauh.components.klipper.menus.klipper_remove_menu import KlipperRemoveMenu
from kiauh.components.mainsail.menus.mainsail_remove_menu import MainsailRemoveMenu
from kiauh.components.moonraker.menus.moonraker_remove_menu import MoonrakerRemoveMenu
from kiauh.utils.constants import COLOR_RED, RESET_FORMAT


# noinspection PyUnusedLocal
# noinspection PyMethodMayBeStatic
class RemoveMenu(BaseMenu):
    def __init__(self):
        super().__init__(
            header=True,
            options={
                "1": KlipperRemoveMenu,
                "2": MoonrakerRemoveMenu,
                "3": MainsailRemoveMenu,
                "5": self.remove_fluidd,
                "6": self.remove_klipperscreen,
                "7": self.remove_crowsnest,
                "8": self.remove_mjpgstreamer,
                "9": self.remove_pretty_gcode,
                "10": self.remove_telegram_bot,
                "11": self.remove_obico,
                "12": self.remove_octoeverywhere,
                "13": self.remove_mobileraker,
                "14": self.remove_nginx,
            },
            footer_type=BACK_FOOTER,
        )

    def print_menu(self):
        header = " [ Remove Menu ] "
        color = COLOR_RED
        count = 62 - len(color) - len(RESET_FORMAT)
        menu = textwrap.dedent(
            f"""
            /=======================================================\\
            | {color}{header:~^{count}}{RESET_FORMAT} |
            |-------------------------------------------------------|
            | INFO: Configurations and/or any backups will be kept! |
            |-------------------------------------------------------|
            | Firmware & API:           | Webcam Streamer:          |
            |  1) [Klipper]             |  6) [Crowsnest]           |
            |  2) [Moonraker]           |  7) [MJPG-Streamer]       |
            |                           |                           |
            | Klipper Webinterface:     | Other:                    |
            |  3) [Mainsail]            |  8) [PrettyGCode]         |
            |  4) [Fluidd]              |  9) [Telegram Bot]        |
            |                           | 10) [Obico for Klipper]   |
            | Touchscreen GUI:          | 11) [OctoEverywhere]      |
            |  5) [KlipperScreen]       | 12) [Mobileraker]         |
            |                           | 13) [NGINX]               |
            |                           |                           |
            """
        )[1:]
        print(menu, end="")

    def remove_fluidd(self, **kwargs):
        print("remove_fluidd")

    def remove_fluidd_config(self, **kwargs):
        print("remove_fluidd_config")

    def remove_klipperscreen(self, **kwargs):
        print("remove_klipperscreen")

    def remove_crowsnest(self, **kwargs):
        print("remove_crowsnest")

    def remove_mjpgstreamer(self, **kwargs):
        print("remove_mjpgstreamer")

    def remove_pretty_gcode(self, **kwargs):
        print("remove_pretty_gcode")

    def remove_telegram_bot(self, **kwargs):
        print("remove_telegram_bot")

    def remove_obico(self, **kwargs):
        print("remove_obico")

    def remove_octoeverywhere(self, **kwargs):
        print("remove_octoeverywhere")

    def remove_mobileraker(self, **kwargs):
        print("remove_mobileraker")

    def remove_nginx(self, **kwargs):
        print("remove_nginx")
