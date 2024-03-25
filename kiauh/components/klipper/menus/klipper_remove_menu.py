# ======================================================================= #
#  Copyright (C) 2020 - 2024 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #

import textwrap

from components.klipper import klipper_remove
from core.menus import BACK_HELP_FOOTER
from core.menus.base_menu import BaseMenu
from utils.constants import RESET_FORMAT, COLOR_RED, COLOR_CYAN


# noinspection PyUnusedLocal
class KlipperRemoveMenu(BaseMenu):
    def __init__(self):
        super().__init__(
            header=False,
            options={
                "0": self.toggle_all,
                "1": self.toggle_remove_klipper_service,
                "2": self.toggle_remove_klipper_dir,
                "3": self.toggle_remove_klipper_env,
                "4": self.toggle_delete_klipper_logs,
                "c": self.run_removal_process,
            },
            footer_type=BACK_HELP_FOOTER,
        )
        self.remove_klipper_service = False
        self.remove_klipper_dir = False
        self.remove_klipper_env = False
        self.delete_klipper_logs = False

    def print_menu(self) -> None:
        header = " [ Remove Klipper ] "
        color = COLOR_RED
        count = 62 - len(color) - len(RESET_FORMAT)
        checked = f"[{COLOR_CYAN}x{RESET_FORMAT}]"
        unchecked = "[ ]"
        o1 = checked if self.remove_klipper_service else unchecked
        o2 = checked if self.remove_klipper_dir else unchecked
        o3 = checked if self.remove_klipper_env else unchecked
        o4 = checked if self.delete_klipper_logs else unchecked
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
            |  4) {o4} Delete all Log-Files                          |
            |-------------------------------------------------------|
            |  C) Continue                                          |
            """
        )[1:]
        print(menu, end="")

    def toggle_all(self, **kwargs) -> None:
        self.remove_klipper_service = True
        self.remove_klipper_dir = True
        self.remove_klipper_env = True
        self.delete_klipper_logs = True

    def toggle_remove_klipper_service(self, **kwargs) -> None:
        self.remove_klipper_service = not self.remove_klipper_service

    def toggle_remove_klipper_dir(self, **kwargs) -> None:
        self.remove_klipper_dir = not self.remove_klipper_dir

    def toggle_remove_klipper_env(self, **kwargs) -> None:
        self.remove_klipper_env = not self.remove_klipper_env

    def toggle_delete_klipper_logs(self, **kwargs) -> None:
        self.delete_klipper_logs = not self.delete_klipper_logs

    def run_removal_process(self, **kwargs) -> None:
        if (
            not self.remove_klipper_service
            and not self.remove_klipper_dir
            and not self.remove_klipper_env
            and not self.delete_klipper_logs
        ):
            error = f"{COLOR_RED}Nothing selected! Select options to remove first.{RESET_FORMAT}"
            print(error)
            return

        klipper_remove.run_klipper_removal(
            self.remove_klipper_service,
            self.remove_klipper_dir,
            self.remove_klipper_env,
            self.delete_klipper_logs,
        )

        self.remove_klipper_service = False
        self.remove_klipper_dir = False
        self.remove_klipper_env = False
        self.delete_klipper_logs = False
