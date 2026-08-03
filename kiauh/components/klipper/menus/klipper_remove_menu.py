# ======================================================================= #
#  Copyright (C) 2020 - 2026 Dominik Willner <dev.dw-0@proton.me>         #
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
from core.i18n import _tr
from core.menus import FooterType, Option
from core.menus.base_menu import BaseMenu
from core.types.color import Color


# noinspection PyUnusedLocal
class KlipperRemoveMenu(BaseMenu):
    def __init__(self, previous_menu: Type[BaseMenu] | None = None):
        super().__init__()

        self.title = _tr("Remove Klipper")
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
        sel_state = _tr("{} everything").format(
            _tr("Select") if not self.select_state else _tr("Deselect")
        )
        menu = textwrap.dedent(
            f"""
            ╟───────────────────────────────────────────────────────╢
            ║ {_tr("Enter a number and hit enter to select / deselect"):<62}║
            ║ {_tr("the specific option for removal."):<62}║
            ╟───────────────────────────────────────────────────────╢
            ║  a) {sel_state:49} ║
            ╟───────────────────────────────────────────────────────╢
            ║  1) {o1} {_tr("Remove Service"):38} ║
            ║  2) {o2} {_tr("Remove Local Repository"):38} ║
            ║  3) {o3} {_tr("Remove Python Environment"):38} ║
            ╟───────────────────────────────────────────────────────╢
            ║  C) {_tr("Continue"):48} ║
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
            msg = _tr("Nothing selected! Select options to remove first.")
            print(Color.apply(msg, Color.RED))
            return

        self.klsvc.remove(self.rm_svc, self.rm_dir, self.rm_env)

        self.rm_svc = False
        self.rm_dir = False
        self.rm_env = False
        self.select_state = False
