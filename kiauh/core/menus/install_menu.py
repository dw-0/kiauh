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

from components.crowsnest.crowsnest import install_crowsnest
from components.klipper.services.klipper_setup_service import KlipperSetupService
from components.klipperscreen.klipperscreen import install_klipperscreen
from components.moonraker.services.moonraker_setup_service import MoonrakerSetupService
from components.webui_client.client_config.client_config_setup import (
    install_client_config,
)
from components.webui_client.client_setup import install_client
from components.webui_client.fluidd_data import FluiddData
from components.webui_client.mainsail_data import MainsailData
from components.webui_client.menus.client_install_menu import ClientInstallMenu
from core.menus import Option
from core.menus.base_menu import BaseMenu
from core.settings.kiauh_settings import KiauhSettings
from core.types.color import Color


# noinspection PyUnusedLocal
# noinspection PyMethodMayBeStatic
class InstallMenu(BaseMenu):
    def __init__(self, previous_menu: Type[BaseMenu] | None = None) -> None:
        super().__init__()
        self.title = "Installation Menu"
        self.title_color = Color.GREEN
        self.previous_menu: Type[BaseMenu] | None = previous_menu
        self.klsvc = KlipperSetupService()
        self.mrsvc = MoonrakerSetupService()

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
            "8": Option(method=self.install_crowsnest),
        }

    def print_menu(self) -> None:
        menu = textwrap.dedent(
            """
            ╟───────────────────────────┬───────────────────────────╢
            ║ Firmware & API:           │ Touchscreen GUI:          ║
            ║  1) [Klipper]             │  7) [KlipperScreen]       ║
            ║  2) [Moonraker]           │                           ║
            ║                           │ Webcam Streamer:          ║
            ║ Webinterface:             │  8) [Crowsnest]           ║
            ║  3) [Mainsail]            │                           ║
            ║  4) [Fluidd]              │                           ║
            ║                           │                           ║
            ║ Client-Config:            │                           ║
            ║  5) [Mainsail-Config]     │                           ║
            ║  6) [Fluidd-Config]       │                           ║
            ╟───────────────────────────┴───────────────────────────╢
            """
        )[1:]
        print(menu, end="")

    def install_klipper(self, **kwargs) -> None:
        self.klsvc.install()

    def install_moonraker(self, **kwargs) -> None:
        self.mrsvc.install()

    def install_mainsail(self, **kwargs) -> None:
        client: MainsailData = MainsailData()
        if client.client_dir.exists():
            ClientInstallMenu(client, self.__class__).run()
        else:
            install_client(client, settings=KiauhSettings())

    def install_mainsail_config(self, **kwargs) -> None:
        install_client_config(MainsailData())

    def install_fluidd(self, **kwargs) -> None:
        client: FluiddData = FluiddData()
        if client.client_dir.exists():
            ClientInstallMenu(client, self.__class__).run()
        else:
            install_client(client, settings=KiauhSettings())

    def install_fluidd_config(self, **kwargs) -> None:
        install_client_config(FluiddData())

    def install_klipperscreen(self, **kwargs) -> None:
        install_klipperscreen()

    def install_crowsnest(self, **kwargs) -> None:
        install_crowsnest()
