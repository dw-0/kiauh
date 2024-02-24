#!/usr/bin/env python3

# ======================================================================= #
#  Copyright (C) 2020 - 2024 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #

import textwrap

from components.fluidd import fluidd_remove
from core.menus import BACK_HELP_FOOTER
from core.menus.base_menu import BaseMenu
from utils.constants import RESET_FORMAT, COLOR_RED, COLOR_CYAN


# noinspection PyUnusedLocal
class FluiddRemoveMenu(BaseMenu):
    def __init__(self):
        super().__init__(
            header=False,
            options={
                "0": self.toggle_all,
                "1": self.toggle_remove_fluidd,
                "2": self.toggle_remove_fl_config,
                "3": self.toggle_remove_updater_section,
                "4": self.toggle_remove_printer_cfg_include,
                "5": self.run_removal_process,
            },
            footer_type=BACK_HELP_FOOTER,
        )
        self.remove_fluidd = False
        self.remove_fl_config = False
        self.remove_updater_section = False
        self.remove_printer_cfg_include = False

    def print_menu(self) -> None:
        header = " [ Remove Fluidd ] "
        color = COLOR_RED
        count = 62 - len(color) - len(RESET_FORMAT)
        checked = f"[{COLOR_CYAN}x{RESET_FORMAT}]"
        unchecked = "[ ]"
        o1 = checked if self.remove_fluidd else unchecked
        o2 = checked if self.remove_fl_config else unchecked
        o3 = checked if self.remove_updater_section else unchecked
        o4 = checked if self.remove_printer_cfg_include else unchecked
        menu = textwrap.dedent(
            f"""
            /=======================================================\\
            | {color}{header:~^{count}}{RESET_FORMAT} |
            |-------------------------------------------------------|
            | Enter a number and hit enter to select / deselect     |
            | the specific option for removal.                      |
            |-------------------------------------------------------|
            |  0) Select everything                                 |
            |-------------------------------------------------------|
            |  1) {o1} Remove Fluidd                                 |
            |  2) {o2} Remove fluidd-config                          |
            |                                                       |
            |  printer.cfg & moonraker.conf                         |
            |  3) {o3} Remove Moonraker update section               |
            |  4) {o4} Remove printer.cfg include                    |
            |-------------------------------------------------------|
            |  5) Continue                                          |
            """
        )[1:]
        print(menu, end="")

    def toggle_all(self, **kwargs) -> None:
        self.remove_fluidd = True
        self.remove_fl_config = True
        self.remove_updater_section = True
        self.remove_printer_cfg_include = True

    def toggle_remove_fluidd(self, **kwargs) -> None:
        self.remove_fluidd = not self.remove_fluidd

    def toggle_remove_fl_config(self, **kwargs) -> None:
        self.remove_fl_config = not self.remove_fl_config

    def toggle_remove_updater_section(self, **kwargs) -> None:
        self.remove_updater_section = not self.remove_updater_section

    def toggle_remove_printer_cfg_include(self, **kwargs) -> None:
        self.remove_printer_cfg_include = not self.remove_printer_cfg_include

    def run_removal_process(self, **kwargs) -> None:
        if (
            not self.remove_fluidd
            and not self.remove_fl_config
            and not self.remove_updater_section
            and not self.remove_printer_cfg_include
        ):
            error = f"{COLOR_RED}Nothing selected! Select options to remove first.{RESET_FORMAT}"
            print(error)
            return

        fluidd_remove.run_fluidd_removal(
            remove_fluidd=self.remove_fluidd,
            remove_fl_config=self.remove_fl_config,
            remove_mr_updater_section=self.remove_updater_section,
            remove_flc_printer_cfg_include=self.remove_printer_cfg_include,
        )

        self.remove_fluidd = False
        self.remove_fl_config = False
        self.remove_updater_section = False
        self.remove_printer_cfg_include = False
