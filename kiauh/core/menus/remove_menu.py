# ======================================================================= #
#  Copyright (C) 2020 - 2025 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #
from __future__ import annotations

import textwrap
from typing import Type

from components.crowsnest.crowsnest import remove_crowsnest
from components.klipper.menus.klipper_remove_menu import KlipperRemoveMenu
from components.klipperscreen.klipperscreen import remove_klipperscreen
from components.moonraker.menus.moonraker_remove_menu import (
    MoonrakerRemoveMenu,
)
from components.webui_client.fluidd_data import FluiddData
from components.webui_client.mainsail_data import MainsailData
from components.webui_client.menus.client_remove_menu import ClientRemoveMenu
from core.menus import Option
from core.menus.base_menu import BaseMenu
from core.types.color import Color


# noinspection PyUnusedLocal
# noinspection PyMethodMayBeStatic
class RemoveMenu(BaseMenu):
    def __init__(self, previous_menu: Type[BaseMenu] | None = None) -> None:
        super().__init__()
        self.title = "Remove Menu"
        self.title_color = Color.RED
        self.previous_menu: Type[BaseMenu] | None = previous_menu

    def set_previous_menu(self, previous_menu: Type[BaseMenu] | None) -> None:
        from core.menus.main_menu import MainMenu

        self.previous_menu = previous_menu if previous_menu is not None else MainMenu

    def set_options(self) -> None:
        self.options = {
            "1": Option(method=self.remove_klipper),
            "2": Option(method=self.remove_moonraker),
            "3": Option(method=self.remove_mainsail),
            "4": Option(method=self.remove_fluidd),
            "5": Option(method=self.remove_klipperscreen),
            "6": Option(method=self.remove_crowsnest),
        }

    def print_menu(self) -> None:
        menu = textwrap.dedent(
            """
            ╟───────────────────────────────────────────────────────╢
            ║ INFO: Configurations and/or any backups will be kept! ║
            ╟───────────────────────────┬───────────────────────────╢
            ║ Firmware & API:           │ Touchscreen GUI:          ║
            ║  1) [Klipper]             │  5) [KlipperScreen]       ║
            ║  2) [Moonraker]           │                           ║
            ║                           │ Webcam Streamer:          ║
            ║ Klipper Webinterface:     │  6) [Crowsnest]           ║
            ║  3) [Mainsail]            │                           ║
            ║  4) [Fluidd]              │                           ║
            ╟───────────────────────────┴───────────────────────────╢
            """
        )[1:]
        print(menu, end="")

    def remove_klipper(self, **kwargs) -> None:
        KlipperRemoveMenu(previous_menu=self.__class__).run()

    def remove_moonraker(self, **kwargs) -> None:
        MoonrakerRemoveMenu(previous_menu=self.__class__).run()

    def remove_mainsail(self, **kwargs) -> None:
        ClientRemoveMenu(previous_menu=self.__class__, client=MainsailData()).run()

    def remove_fluidd(self, **kwargs) -> None:
        ClientRemoveMenu(previous_menu=self.__class__, client=FluiddData()).run()

    def remove_klipperscreen(self, **kwargs) -> None:
        remove_klipperscreen()

    def remove_crowsnest(self, **kwargs) -> None:
        remove_crowsnest()
