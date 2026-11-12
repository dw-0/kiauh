# ======================================================================= #
#  Copyright (C) 2020 - 2026 Dominik Willner <dev.dw-0@proton.me>         #
#  Copyright (C) 2026 Théo Gaillard <theo.gayar@gmail.com>                #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #
from __future__ import annotations

import textwrap
from typing import Type

from components.katapult.klipper_flashing import (
    flash_klipper_via_katapult,
    forget_mcu,
    load_remembered_mcus,
    update_all_mcus,
)
from core.menus import FooterType, Option
from core.menus.base_menu import BaseMenu
from core.types.color import Color


# noinspection PyUnusedLocal
# noinspection PyMethodMayBeStatic
class KatapultFlashKlipperMenu(BaseMenu):
    def __init__(self, previous_menu: Type[BaseMenu] | None = None):
        super().__init__()
        self.title = "Flash Klipper Menu"
        self.title_color = Color.CYAN
        self.footer_type = FooterType.BACK

    def set_previous_menu(self, previous_menu: Type[BaseMenu] | None) -> None:
        from core.menus.advanced_menu import AdvancedMenu

        self.previous_menu = (
            previous_menu if previous_menu is not None else AdvancedMenu
        )

    def set_options(self) -> None:
        self.options = {
            "1": Option(self.flash_mcu),
            "2": Option(self.update_all_mcus),
            "3": Option(self.forget_mcu),
        }

    def print_menu(self) -> None:
        count = len(load_remembered_mcus())
        remembered = Color.apply(f"Remembered MCUs: {count}", Color.CYAN)
        menu = textwrap.dedent(
            f"""
            ╟───────────────────────────────────────────────────────╢
            ║ Flash the Klipper firmware through Katapult.          ║
            ║                                                       ║
            ║ MCUs flashed with a firmware built from a saved       ║
            ║ config can be remembered, to rebuild and flash all of ║
            ║ them at once after a Klipper update.                  ║
            ║                                                       ║
            ║ {remembered:<62} ║
            ╟───────────────────────────────────────────────────────╢
            ║ 1) Flash Klipper to an MCU                            ║
            ║ 2) Update all remembered MCUs                         ║
            ║ 3) Forget a remembered MCU                            ║
            ╟───────────────────────────────────────────────────────╢
            """
        )[1:]
        print(menu, end="")

    def flash_mcu(self, **kwargs) -> None:
        flash_klipper_via_katapult()

    def update_all_mcus(self, **kwargs) -> None:
        update_all_mcus()

    def forget_mcu(self, **kwargs) -> None:
        forget_mcu()
