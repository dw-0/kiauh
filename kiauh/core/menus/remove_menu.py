# ======================================================================= #
#  Copyright (C) 2020 - 2024 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #

import textwrap

from components.klipper.menus.klipper_remove_menu import KlipperRemoveMenu
from components.moonraker.menus.moonraker_remove_menu import (
    MoonrakerRemoveMenu,
)
from components.webui_client.client_utils import load_client_data
from components.webui_client.menus.client_remove_menu import ClientRemoveMenu
from core.menus.base_menu import BaseMenu
from utils.constants import COLOR_RED, RESET_FORMAT


# noinspection PyUnusedLocal
# noinspection PyMethodMayBeStatic
class RemoveMenu(BaseMenu):
    def __init__(self, previous_menu: BaseMenu):
        super().__init__()

        self.previous_menu: BaseMenu = previous_menu
        self.options = {
            "1": lambda: KlipperRemoveMenu(previous_menu=self).run(),
            "2": lambda: MoonrakerRemoveMenu(previous_menu=self).run(),
            "3": lambda: ClientRemoveMenu(
                previous_menu=self, client=load_client_data("mainsail")
            ).run(),
            "4": lambda: ClientRemoveMenu(
                previous_menu=self, client=load_client_data("fluidd")
            ).run(),
            "5": None,
            "6": None,
            "7": None,
            "8": None,
            "9": None,
            "10": None,
            "11": None,
            "12": None,
            "13": None,
        }

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
