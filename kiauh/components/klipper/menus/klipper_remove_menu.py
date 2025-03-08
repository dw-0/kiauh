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

from components.klipper.services.klipper_setup_service import KlipperSetupService
from core.menus import FooterType, Option
from core.menus.base_menu import BaseMenu
from core.types.color import Color


# noinspection PyUnusedLocal
class KlipperRemoveMenu(BaseMenu):
    def __init__(self, previous_menu: Type[BaseMenu] | None = None):
        super().__init__()

        self.title = "Remove Klipper"
        self.title_color = Color.RED
        self.previous_menu: Type[BaseMenu] | None = previous_menu
        self.footer_type = FooterType.BACK

        self.rm_svc = False
        self.rm_dir = False
        self.rm_env = False
        self.select_state = False

        self.klsvc = KlipperSetupService()

    def set_previous_menu(self, previous_menu: Type[BaseMenu] | None) -> None:
        from core.menus.remove_menu import RemoveMenu

        self.previous_menu = previous_menu if previous_menu is not None else RemoveMenu

    def set_options(self) -> None:
        self.options = {
            "a": Option(method=self.toggle_all),
            "1": Option(method=self.toggle_remove_klipper_service),
            "2": Option(method=self.toggle_remove_klipper_dir),
            "3": Option(method=self.toggle_remove_klipper_env),
            "c": Option(method=self.run_removal_process),
        }

    def print_menu(self) -> None:
        checked = f"[{Color.apply('x', Color.CYAN)}]"
        unchecked = "[ ]"
        o1 = checked if self.rm_svc else unchecked
        o2 = checked if self.rm_dir else unchecked
        o3 = checked if self.rm_env else unchecked
        sel_state = f"{'Select' if not self.select_state else 'Deselect'} everything"
        menu = textwrap.dedent(
            f"""
            ╟───────────────────────────────────────────────────────╢
            ║ Enter a number and hit enter to select / deselect     ║
            ║ the specific option for removal.                      ║
            ╟───────────────────────────────────────────────────────╢
            ║  a) {sel_state:49} ║
            ╟───────────────────────────────────────────────────────╢
            ║  1) {o1} Remove Service                                ║
            ║  2) {o2} Remove Local Repository                       ║
            ║  3) {o3} Remove Python Environment                     ║
            ╟───────────────────────────────────────────────────────╢
            ║  C) Continue                                          ║
            ╟───────────────────────────────────────────────────────╢
            """
        )[1:]
        print(menu, end="")

    def toggle_all(self, **kwargs) -> None:
        self.select_state = not self.select_state
        self.rm_svc = self.select_state
        self.rm_dir = self.select_state
        self.rm_env = self.select_state

    def toggle_remove_klipper_service(self, **kwargs) -> None:
        self.rm_svc = not self.rm_svc

    def toggle_remove_klipper_dir(self, **kwargs) -> None:
        self.rm_dir = not self.rm_dir

    def toggle_remove_klipper_env(self, **kwargs) -> None:
        self.rm_env = not self.rm_env

    def run_removal_process(self, **kwargs) -> None:
        if not self.rm_svc and not self.rm_dir and not self.rm_env:
            msg = "Nothing selected! Select options to remove first."
            print(Color.apply(msg, Color.RED))
            return

        self.klsvc.remove(self.rm_svc, self.rm_dir, self.rm_env)

        self.rm_svc = False
        self.rm_dir = False
        self.rm_env = False
        self.select_state = False
