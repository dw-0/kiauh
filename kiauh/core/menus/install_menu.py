# ======================================================================= #
#  Copyright (C) 2020 - 2024 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #
from __future__ import annotations

import textwrap
from typing import Type

from components.crowsnest.crowsnest import install_crowsnest
from components.klipper import klipper_setup
from components.klipperscreen.klipperscreen import install_klipperscreen
from components.mobileraker.mobileraker import install_mobileraker
from components.moonraker import moonraker_setup
from components.octoeverywhere.octoeverywhere_setup import install_octoeverywhere
from components.webui_client import client_setup
from components.webui_client.client_config import client_config_setup
from components.webui_client.fluidd_data import FluiddData
from components.webui_client.mainsail_data import MainsailData
from core.constants import COLOR_GREEN, RESET_FORMAT
from core.menus import Option
from core.menus.base_menu import BaseMenu


# noinspection PyUnusedLocal
# noinspection PyMethodMayBeStatic
class InstallMenu(BaseMenu):
    def __init__(self, previous_menu: Type[BaseMenu] | None = None) -> None:
        super().__init__()
        self.previous_menu: Type[BaseMenu] | None = previous_menu

    def set_previous_menu(self, previous_menu: Type[BaseMenu] | None) -> None:
        from core.menus.main_menu import MainMenu

        self.previous_menu = previous_menu if previous_menu is not None else MainMenu

    def set_options(self) -> None:
        self.options = {
            "1": Option(method=self.install_klipper),
            "2": Option(method=self.install_moonraker),
            "3": Option(method=self.install_mainsail),
            "4": Option(method=self.install_fluidd),
            "5": Option(method=self.install_mainsail_config),
            "6": Option(method=self.install_fluidd_config),
            "7": Option(method=self.install_klipperscreen),
            "8": Option(method=self.install_mobileraker),
            "9": Option(method=self.install_crowsnest),
            "10": Option(method=self.install_octoeverywhere),
        }

    def print_menu(self) -> None:
        header = " [ Installation Menu ] "
        color = COLOR_GREEN
        count = 62 - len(color) - len(RESET_FORMAT)
        menu = textwrap.dedent(
            f"""
            ╔═══════════════════════════════════════════════════════╗
            ║ {color}{header:~^{count}}{RESET_FORMAT} ║
            ╟───────────────────────────┬───────────────────────────╢
            ║ Firmware & API:           │ Touchscreen GUI:          ║
            ║  1) [Klipper]             │  7) [KlipperScreen]       ║
            ║  2) [Moonraker]           │                           ║
            ║                           │ Android / iOS:            ║
            ║ Webinterface:             │  8) [Mobileraker]         ║
            ║  3) [Mainsail]            │                           ║
            ║  4) [Fluidd]              │ Webcam Streamer:          ║
            ║                           │  9) [Crowsnest]           ║
            ║ Client-Config:            │                           ║
            ║  5) [Mainsail-Config]     │ Remote Access:            ║
            ║  6) [Fluidd-Config]       │ 10) [OctoEverywhere]      ║
            ║                           │                           ║
            ╟───────────────────────────┴───────────────────────────╢
            """
        )[1:]
        print(menu, end="")

    def install_klipper(self, **kwargs) -> None:
        klipper_setup.install_klipper()

    def install_moonraker(self, **kwargs) -> None:
        moonraker_setup.install_moonraker()

    def install_mainsail(self, **kwargs) -> None:
        client_setup.install_client(MainsailData())

    def install_mainsail_config(self, **kwargs) -> None:
        client_config_setup.install_client_config(MainsailData())

    def install_fluidd(self, **kwargs) -> None:
        client_setup.install_client(FluiddData())

    def install_fluidd_config(self, **kwargs) -> None:
        client_config_setup.install_client_config(FluiddData())

    def install_klipperscreen(self, **kwargs) -> None:
        install_klipperscreen()

    def install_mobileraker(self, **kwargs) -> None:
        install_mobileraker()

    def install_crowsnest(self, **kwargs) -> None:
        install_crowsnest()

    def install_octoeverywhere(self, **kwargs) -> None:
        install_octoeverywhere()
