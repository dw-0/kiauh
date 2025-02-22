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

from components.klipper.klipper_utils import backup_klipper_dir
from components.klipperscreen.klipperscreen import backup_klipperscreen_dir
from components.moonraker.utils.utils import (
    backup_moonraker_db_dir,
    backup_moonraker_dir,
)
from components.webui_client.client_utils import (
    backup_client_config_data,
    backup_client_data,
)
from components.webui_client.fluidd_data import FluiddData
from components.webui_client.mainsail_data import MainsailData
from core.menus import Option
from core.menus.base_menu import BaseMenu
from core.types.color import Color
from utils.common import backup_printer_config_dir


# noinspection PyUnusedLocal
# noinspection PyMethodMayBeStatic
class BackupMenu(BaseMenu):
    def __init__(self, previous_menu: Type[BaseMenu] | None = None) -> None:
        super().__init__()
        self.title = "Backup Menu"
        self.title_color = Color.GREEN
        self.previous_menu: Type[BaseMenu] | None = previous_menu

    def set_previous_menu(self, previous_menu: Type[BaseMenu] | None) -> None:
        from core.menus.main_menu import MainMenu

        self.previous_menu = previous_menu if previous_menu is not None else MainMenu

    def set_options(self) -> None:
        self.options = {
            "1": Option(method=self.backup_klipper),
            "2": Option(method=self.backup_moonraker),
            "3": Option(method=self.backup_printer_config),
            "4": Option(method=self.backup_moonraker_db),
            "5": Option(method=self.backup_mainsail),
            "6": Option(method=self.backup_fluidd),
            "7": Option(method=self.backup_mainsail_config),
            "8": Option(method=self.backup_fluidd_config),
            "9": Option(method=self.backup_klipperscreen),
        }

    def print_menu(self) -> None:
        line1 = Color.apply(
            "INFO: Backups are located in '~/kiauh-backups'", Color.YELLOW
        )
        menu = textwrap.dedent(
            f"""
            ╟───────────────────────────────────────────────────────╢
            ║ {line1:^62} ║
            ╟───────────────────────────┬───────────────────────────╢
            ║ Klipper & Moonraker API:  │ Client-Config:            ║
            ║  1) [Klipper]             │  7) [Mainsail-Config]     ║
            ║  2) [Moonraker]           │  8) [Fluidd-Config]       ║
            ║  3) [Config Folder]       │                           ║
            ║  4) [Moonraker Database]  │ Touchscreen GUI:          ║
            ║                           │  9) [KlipperScreen]       ║
            ║ Webinterface:             │                           ║
            ║  5) [Mainsail]            │                           ║
            ║  6) [Fluidd]              │                           ║
            ╟───────────────────────────┴───────────────────────────╢
            """
        )[1:]
        print(menu, end="")

    def backup_klipper(self, **kwargs) -> None:
        backup_klipper_dir()

    def backup_moonraker(self, **kwargs) -> None:
        backup_moonraker_dir()

    def backup_printer_config(self, **kwargs) -> None:
        backup_printer_config_dir()

    def backup_moonraker_db(self, **kwargs) -> None:
        backup_moonraker_db_dir()

    def backup_mainsail(self, **kwargs) -> None:
        backup_client_data(MainsailData())

    def backup_fluidd(self, **kwargs) -> None:
        backup_client_data(FluiddData())

    def backup_mainsail_config(self, **kwargs) -> None:
        backup_client_config_data(MainsailData())

    def backup_fluidd_config(self, **kwargs) -> None:
        backup_client_config_data(FluiddData())

    def backup_klipperscreen(self, **kwargs) -> None:
        backup_klipperscreen_dir()
