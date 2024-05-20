# ======================================================================= #
#  Copyright (C) 2020 - 2024 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #

import textwrap
from typing import Optional, Type

from components.crowsnest.crowsnest import remove_crowsnest
from components.klipper.menus.klipper_remove_menu import KlipperRemoveMenu
from components.klipperscreen.klipperscreen import remove_klipperscreen
from components.mobileraker.mobileraker import remove_mobileraker
from components.moonraker.menus.moonraker_remove_menu import (
    MoonrakerRemoveMenu,
)
from components.webui_client.fluidd_data import FluiddData
from components.webui_client.mainsail_data import MainsailData
from components.webui_client.menus.client_remove_menu import ClientRemoveMenu
from core.menus import Option
from core.menus.base_menu import BaseMenu
from utils.constants import COLOR_RED, RESET_FORMAT


# noinspection PyUnusedLocal
# noinspection PyMethodMayBeStatic
class RemoveMenu(BaseMenu):
    def __init__(self, previous_menu: Optional[Type[BaseMenu]] = None):
        super().__init__()
        self.previous_menu = previous_menu

    def set_previous_menu(self, previous_menu: Optional[Type[BaseMenu]]) -> None:
        from core.menus.main_menu import MainMenu

        self.previous_menu: Type[BaseMenu] = (
            previous_menu if previous_menu is not None else MainMenu
        )

    def set_options(self):
        self.options = {
            "1": Option(method=self.remove_klipper, menu=True),
            "2": Option(method=self.remove_moonraker, menu=True),
            "3": Option(method=self.remove_mainsail, menu=True),
            "4": Option(method=self.remove_fluidd, menu=True),
            "5": Option(method=self.remove_klipperscreen, menu=True),
            "6": Option(method=self.remove_mobileraker, menu=True),
            "7": Option(method=self.remove_crowsnest, menu=True),
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
            | Firmware & API:           | Touchscreen GUI:          |
            |  1) [Klipper]             |  5) [KlipperScreen]       |
            |  2) [Moonraker]           |                           |
            |                           | Android / iOS:            |
            | Klipper Webinterface:     |  6) [Mobileraker]         |
            |  3) [Mainsail]            |                           |
            |  4) [Fluidd]              | Webcam Streamer:          |
            |                           |  7) [Crowsnest]           |
            """
        )[1:]
        print(menu, end="")

    def remove_klipper(self, **kwargs):
        KlipperRemoveMenu(previous_menu=self.__class__).run()

    def remove_moonraker(self, **kwargs):
        MoonrakerRemoveMenu(previous_menu=self.__class__).run()

    def remove_mainsail(self, **kwargs):
        ClientRemoveMenu(previous_menu=self.__class__, client=MainsailData()).run()

    def remove_fluidd(self, **kwargs):
        ClientRemoveMenu(previous_menu=self.__class__, client=FluiddData()).run()

    def remove_klipperscreen(self, **kwargs):
        remove_klipperscreen()

    def remove_mobileraker(self, **kwargs):
        remove_mobileraker()

    def remove_crowsnest(self, **kwargs):
        remove_crowsnest()
