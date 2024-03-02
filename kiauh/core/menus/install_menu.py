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

from components.klipper import klipper_setup
from components.moonraker import moonraker_setup
from components.webui_client import client_setup
from components.webui_client.client_config import client_config_setup
from core.menus import BACK_FOOTER
from core.menus.base_menu import BaseMenu
from utils.constants import COLOR_GREEN, RESET_FORMAT


# noinspection PyUnusedLocal
# noinspection PyMethodMayBeStatic
class InstallMenu(BaseMenu):
    def __init__(self):
        super().__init__(
            header=True,
            options={
                "1": self.install_klipper,
                "2": self.install_moonraker,
                "3": self.install_mainsail,
                "4": self.install_fluidd,
                "5": self.install_mainsail_config,
                "6": self.install_fluidd_config,
                "7": None,
                "8": None,
                "9": None,
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
            | Firmware & API:           | Touchscreen GUI:          |
            |  1) [Klipper]             |  7) [KlipperScreen]       |
            |  2) [Moonraker]           |                           |
            |                           | Android / iOS:            |
            | Webinterface:             |  8) [Mobileraker]         |
            |  3) [Mainsail]            |                           |
            |  4) [Fluidd]              | Webcam Streamer:          |
            |                           |  9) [Crowsnest]           |
            | Client-Config:            |                           |
            |  5) [Mainsail-Config]     |                           |
            |  6) [Fluidd-Config]       |                           |
            |                           |                           |
            """
        )[1:]
        print(menu, end="")

    def install_klipper(self, **kwargs):
        klipper_setup.install_klipper()

    def install_moonraker(self, **kwargs):
        moonraker_setup.install_moonraker()

    def install_mainsail(self, **kwargs):
        client_setup.install_client(client_name="mainsail")

    def install_mainsail_config(self, **kwargs):
        client_config_setup.install_client_config(client_name="mainsail")

    def install_fluidd(self, **kwargs):
        client_setup.install_client(client_name="fluidd")

    def install_fluidd_config(self, **kwargs):
        client_config_setup.install_client_config(client_name="fluidd")
