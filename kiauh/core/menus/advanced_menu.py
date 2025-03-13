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

from components.klipper import KLIPPER_DIR
from components.klipper.klipper import Klipper
from components.klipper.klipper_utils import install_input_shaper_deps
from components.klipper_firmware.menus.klipper_build_menu import (
    KlipperBuildFirmwareMenu,
    KlipperKConfigMenu,
)
from components.klipper_firmware.menus.klipper_flash_menu import (
    KlipperFlashMethodMenu,
    KlipperSelectMcuConnectionMenu,
)
from components.moonraker import MOONRAKER_DIR
from components.moonraker.moonraker import Moonraker
from core.menus import Option
from core.menus.base_menu import BaseMenu
from core.types.color import Color
from procedures.system import change_system_hostname
from utils.git_utils import rollback_repository


# noinspection PyUnusedLocal
# noinspection PyMethodMayBeStatic
class AdvancedMenu(BaseMenu):
    def __init__(self, previous_menu: Type[BaseMenu] | None = None) -> None:
        super().__init__()
        self.title = "Advanced Menu"
        self.title_color = Color.YELLOW
        self.previous_menu: Type[BaseMenu] | None = previous_menu

    def set_previous_menu(self, previous_menu: Type[BaseMenu] | None) -> None:
        from core.menus.main_menu import MainMenu

        self.previous_menu = previous_menu if previous_menu is not None else MainMenu

    def set_options(self) -> None:
        self.options = {
            "1": Option(method=self.build),
            "2": Option(method=self.flash),
            "3": Option(method=self.build_flash),
            "4": Option(method=self.get_id),
            "5": Option(method=self.input_shaper),
            "6": Option(method=self.klipper_rollback),
            "7": Option(method=self.moonraker_rollback),
            "8": Option(method=self.change_hostname),
        }

    def print_menu(self) -> None:
        menu = textwrap.dedent(
            """
            ╟───────────────────────────┬───────────────────────────╢
            ║ Klipper Firmware:         │ Repository Rollback:      ║
            ║  1) [Build]               │  6) [Klipper]             ║
            ║  2) [Flash]               │  7) [Moonraker]           ║
            ║  3) [Build + Flash]       │                           ║
            ║  4) [Get MCU ID]          │ System:                   ║
            ║                           │  8) [Change hostname]     ║
            ║ Extra Dependencies:       │                           ║
            ║  5) [Input Shaper]        │                           ║
            ╟───────────────────────────┴───────────────────────────╢
            """
        )[1:]
        print(menu, end="")

    def klipper_rollback(self, **kwargs) -> None:
        rollback_repository(KLIPPER_DIR, Klipper)

    def moonraker_rollback(self, **kwargs) -> None:
        rollback_repository(MOONRAKER_DIR, Moonraker)

    def build(self, **kwargs) -> None:
        KlipperKConfigMenu().run()
        KlipperBuildFirmwareMenu(previous_menu=self.__class__).run()

    def flash(self, **kwargs) -> None:
        KlipperKConfigMenu().run()
        KlipperFlashMethodMenu(previous_menu=self.__class__).run()

    def build_flash(self, **kwargs) -> None:
        KlipperKConfigMenu().run()
        KlipperBuildFirmwareMenu(previous_menu=KlipperFlashMethodMenu).run()
        KlipperFlashMethodMenu(previous_menu=self.__class__).run()

    def get_id(self, **kwargs) -> None:
        KlipperSelectMcuConnectionMenu(
            previous_menu=self.__class__,
            standalone=True,
        ).run()

    def change_hostname(self, **kwargs) -> None:
        change_system_hostname()

    def input_shaper(self, **kwargs) -> None:
        install_input_shaper_deps()
