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

from kiauh.core.menus import BACK_HELP_FOOTER
from kiauh.core.menus.base_menu import BaseMenu
from kiauh.modules.mainsail import mainsail_remove
from kiauh.utils.constants import RESET_FORMAT, COLOR_RED, COLOR_CYAN


class MainsailRemoveMenu(BaseMenu):
    def __init__(self):
        super().__init__(
            header=False,
            options={
                0: self.toggle_all,
                1: self.toggle_remove_mainsail,
                2: self.toggle_remove_ms_config,
                3: self.toggle_backup_config_json,
                4: self.toggle_remove_updater_section,
                5: self.toggle_remove_printer_cfg_include,
                6: self.run_removal_process,
            },
            footer_type=BACK_HELP_FOOTER,
        )
        self.remove_mainsail = False
        self.remove_ms_config = False
        self.backup_config_json = False
        self.remove_updater_section = False
        self.remove_printer_cfg_include = False

    def print_menu(self) -> None:
        header = " [ Remove Mainsail ] "
        color = COLOR_RED
        count = 62 - len(color) - len(RESET_FORMAT)
        checked = f"[{COLOR_CYAN}x{RESET_FORMAT}]"
        unchecked = "[ ]"
        o1 = checked if self.remove_mainsail else unchecked
        o2 = checked if self.remove_ms_config else unchecked
        o3 = checked if self.backup_config_json else unchecked
        o4 = checked if self.remove_updater_section else unchecked
        o5 = checked if self.remove_printer_cfg_include else unchecked
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
            |  1) {o1} Remove Mainsail                               |
            |  2) {o2} Remove mainsail-config                        |
            |  3) {o3} Backup config.json                            |
            |                                                       |
            |  printer.cfg & moonraker.conf                         |
            |  4) {o4} Remove Moonraker update section               |
            |  5) {o5} Remove printer.cfg include                    |
            |-------------------------------------------------------|
            |  6) Continue                                          |
            """
        )[1:]
        print(menu, end="")

    def toggle_all(self) -> None:
        self.remove_mainsail = True
        self.remove_ms_config = True
        self.backup_config_json = True
        self.remove_updater_section = True
        self.remove_printer_cfg_include = True

    def toggle_remove_mainsail(self) -> None:
        self.remove_mainsail = not self.remove_mainsail

    def toggle_remove_ms_config(self) -> None:
        self.remove_ms_config = not self.remove_ms_config

    def toggle_backup_config_json(self) -> None:
        self.backup_config_json = not self.backup_config_json

    def toggle_remove_updater_section(self) -> None:
        self.remove_updater_section = not self.remove_updater_section

    def toggle_remove_printer_cfg_include(self) -> None:
        self.remove_printer_cfg_include = not self.remove_printer_cfg_include

    def run_removal_process(self) -> None:
        if (
            not self.remove_mainsail
            and not self.remove_ms_config
            and not self.backup_config_json
            and not self.remove_updater_section
            and not self.remove_printer_cfg_include
        ):
            error = f"{COLOR_RED}Nothing selected! Select options to remove first.{RESET_FORMAT}"
            print(error)
            return

        mainsail_remove.run_mainsail_removal(
            remove_mainsail=self.remove_mainsail,
            remove_ms_config=self.remove_ms_config,
            backup_ms_config_json=self.backup_config_json,
            remove_mr_updater_section=self.remove_updater_section,
            remove_msc_printer_cfg_include=self.remove_printer_cfg_include,
        )

        self.remove_mainsail = False
        self.remove_ms_config = False
        self.backup_config_json = False
        self.remove_updater_section = False
        self.remove_printer_cfg_include = False
