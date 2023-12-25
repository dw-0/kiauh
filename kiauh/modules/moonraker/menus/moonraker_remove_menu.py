#!/usr/bin/env python3

# ======================================================================= #
#  Copyright (C) 2020 - 2023 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #

import textwrap

from kiauh.core.menus import BACK_HELP_FOOTER
from kiauh.core.menus.base_menu import BaseMenu
from kiauh.modules.moonraker import moonraker_remove
from kiauh.utils.constants import RESET_FORMAT, COLOR_RED, COLOR_CYAN


class MoonrakerRemoveMenu(BaseMenu):
    def __init__(self):
        super().__init__(
            header=False,
            options={
                0: self.toggle_all,
                1: self.toggle_remove_moonraker_service,
                2: self.toggle_remove_moonraker_dir,
                3: self.toggle_remove_moonraker_env,
                4: self.toggle_remove_moonraker_polkit,
                5: self.toggle_delete_moonraker_logs,
                6: self.run_removal_process,
            },
            footer_type=BACK_HELP_FOOTER,
        )
        self.remove_moonraker_service = False
        self.remove_moonraker_dir = False
        self.remove_moonraker_env = False
        self.remove_moonraker_polkit = False
        self.delete_moonraker_logs = False

    def print_menu(self) -> None:
        header = " [ Remove Moonraker ] "
        color = COLOR_RED
        count = 62 - len(color) - len(RESET_FORMAT)
        checked = f"[{COLOR_CYAN}x{RESET_FORMAT}]"
        unchecked = "[ ]"
        o1 = checked if self.remove_moonraker_service else unchecked
        o2 = checked if self.remove_moonraker_dir else unchecked
        o3 = checked if self.remove_moonraker_env else unchecked
        o4 = checked if self.remove_moonraker_polkit else unchecked
        o5 = checked if self.delete_moonraker_logs else unchecked
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
            |  1) {o1} Remove Service                                |
            |  2) {o2} Remove Local Repository                       |
            |  3) {o3} Remove Python Environment                     |
            |  4) {o4} Remove Policy Kit Rules                       |
            |  5) {o5} Delete all Log-Files                          |
            |-------------------------------------------------------|
            |  6) Continue                                          |
            """
        )[1:]
        print(menu, end="")

    def toggle_all(self) -> None:
        self.remove_moonraker_service = True
        self.remove_moonraker_dir = True
        self.remove_moonraker_env = True
        self.remove_moonraker_polkit = True
        self.delete_moonraker_logs = True

    def toggle_remove_moonraker_service(self) -> None:
        self.remove_moonraker_service = not self.remove_moonraker_service

    def toggle_remove_moonraker_dir(self) -> None:
        self.remove_moonraker_dir = not self.remove_moonraker_dir

    def toggle_remove_moonraker_env(self) -> None:
        self.remove_moonraker_env = not self.remove_moonraker_env

    def toggle_remove_moonraker_polkit(self) -> None:
        self.remove_moonraker_polkit = not self.remove_moonraker_polkit

    def toggle_delete_moonraker_logs(self) -> None:
        self.delete_moonraker_logs = not self.delete_moonraker_logs

    def run_removal_process(self) -> None:
        if (
            not self.remove_moonraker_service
            and not self.remove_moonraker_dir
            and not self.remove_moonraker_env
            and not self.remove_moonraker_polkit
            and not self.delete_moonraker_logs
        ):
            error = f"{COLOR_RED}Nothing selected! Select options to remove first.{RESET_FORMAT}"
            print(error)
            return

        moonraker_remove.run_moonraker_removal(
            self.remove_moonraker_service,
            self.remove_moonraker_dir,
            self.remove_moonraker_env,
            self.remove_moonraker_polkit,
            self.delete_moonraker_logs,
        )

        self.remove_moonraker_service = False
        self.remove_moonraker_dir = False
        self.remove_moonraker_env = False
        self.remove_moonraker_polkit = False
        self.delete_moonraker_logs = False
