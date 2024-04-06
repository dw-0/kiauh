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
from components.webui_client.fluidd_data import FluiddData
from components.webui_client.mainsail_data import MainsailData

from core.menus.base_menu import BaseMenu
from utils.constants import COLOR_GREEN, RESET_FORMAT


# noinspection PyUnusedLocal
# noinspection PyMethodMayBeStatic
class InstallMenu(BaseMenu):
    def __init__(self, previous_menu: BaseMenu):
        super().__init__()

        self.previous_menu: BaseMenu = previous_menu
        self.options = {
            "1": self.install_klipper,
            "2": self.install_moonraker,
            "3": self.install_mainsail,
            "4": self.install_fluidd,
            "5": self.install_mainsail_config,
            "6": self.install_fluidd_config,
            "7": None,
            "8": None,
            "9": None,
        }

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
        client_setup.install_client(MainsailData())

    def install_mainsail_config(self, **kwargs):
        client_config_setup.install_client_config(MainsailData())

    def install_fluidd(self, **kwargs):
        client_setup.install_client(FluiddData())

    def install_fluidd_config(self, **kwargs):
        client_config_setup.install_client_config(FluiddData())
