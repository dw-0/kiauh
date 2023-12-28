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

from kiauh.core.menus import QUIT_FOOTER
from kiauh.core.menus.advanced_menu import AdvancedMenu
from kiauh.core.menus.base_menu import BaseMenu
from kiauh.core.menus.install_menu import InstallMenu
from kiauh.core.menus.remove_menu import RemoveMenu
from kiauh.core.menus.settings_menu import SettingsMenu
from kiauh.core.menus.update_menu import UpdateMenu
from kiauh.modules.klipper.klipper_utils import get_klipper_status
from kiauh.modules.mainsail.mainsail_utils import get_mainsail_status
from kiauh.modules.moonraker.moonraker_utils import get_moonraker_status
from kiauh.utils.constants import (
    COLOR_MAGENTA,
    COLOR_CYAN,
    RESET_FORMAT,
    COLOR_RED,
    COLOR_GREEN,
    COLOR_YELLOW,
)


class MainMenu(BaseMenu):
    def __init__(self):
        super().__init__(
            header=True,
            options={
                0: None,
                1: InstallMenu,
                2: UpdateMenu,
                3: RemoveMenu,
                4: AdvancedMenu,
                5: None,
                6: SettingsMenu,
            },
            footer_type=QUIT_FOOTER,
        )
        self.kl_status = ""
        self.kl_repo = ""
        self.mr_status = ""
        self.mr_repo = ""
        self.ms_status = ""
        self.fl_status = ""
        self.ks_status = ""
        self.mb_status = ""
        self.cn_status = ""
        self.tg_status = ""
        self.ob_status = ""
        self.oe_status = ""
        self.init_status()

    def init_status(self) -> None:
        status_vars = ["kl", "mr", "ms", "fl", "ks", "mb", "cn", "tg", "ob", "oe"]
        for var in status_vars:
            setattr(self, f"{var}_status", f"{COLOR_RED}Not installed!{RESET_FORMAT}")

    def fetch_status(self) -> None:
        # klipper
        klipper_status = get_klipper_status()
        kl_status = klipper_status.get("status")
        kl_code = klipper_status.get("status_code")
        kl_instances = f" {klipper_status.get('instances')}" if kl_code == 1 else ""
        self.kl_status = self.format_status_by_code(kl_code, kl_status, kl_instances)
        self.kl_repo = f"{COLOR_CYAN}{klipper_status.get('repo')}{RESET_FORMAT}"
        # moonraker
        moonraker_status = get_moonraker_status()
        mr_status = moonraker_status.get("status")
        mr_code = moonraker_status.get("status_code")
        mr_instances = f" {moonraker_status.get('instances')}" if mr_code == 1 else ""
        self.mr_status = self.format_status_by_code(mr_code, mr_status, mr_instances)
        self.mr_repo = f"{COLOR_CYAN}{moonraker_status.get('repo')}{RESET_FORMAT}"
        # mainsail
        self.ms_status = get_mainsail_status()

    def format_status_by_code(self, code: int, status: str, count: str) -> str:
        if code == 1:
            return f"{COLOR_GREEN}{status}{count}{RESET_FORMAT}"
        elif code == 2:
            return f"{COLOR_RED}{status}{count}{RESET_FORMAT}"

        return f"{COLOR_YELLOW}{status}{count}{RESET_FORMAT}"

    def print_menu(self):
        self.fetch_status()

        header = " [ Main Menu ] "
        footer1 = "KIAUH v6.0.0"
        footer2 = f"Changelog: {COLOR_MAGENTA}https://git.io/JnmlX{RESET_FORMAT}"
        color = COLOR_CYAN
        count = 62 - len(color) - len(RESET_FORMAT)
        menu = textwrap.dedent(
            f"""
            /=======================================================\\
            | {color}{header:~^{count}}{RESET_FORMAT} |
            |-------------------------------------------------------|
            |  0) [Log-Upload] |   Klipper: {self.kl_status:<32} |
            |                  |      Repo: {self.kl_repo:<32} |
            |  1) [Install]    |------------------------------------|
            |  2) [Update]     | Moonraker: {self.mr_status:<32} |
            |  3) [Remove]     |      Repo: {self.mr_repo:<32} |
            |  4) [Advanced]   |------------------------------------|
            |  5) [Backup]     |        Mainsail: {self.ms_status:<26} |
            |                  |          Fluidd: {self.fl_status:<26} |
            |  6) [Settings]   |   KlipperScreen: {self.ks_status:<26} |
            |                  |     Mobileraker: {self.mb_status:<26} |
            |                  |                                    |
            |                  |       Crowsnest: {self.cn_status:<26} |
            |                  |    Telegram Bot: {self.tg_status:<26} |
            |                  |           Obico: {self.ob_status:<26} |
            |                  |  OctoEverywhere: {self.oe_status:<26} |
            |-------------------------------------------------------|
            | {COLOR_CYAN}{footer1:^16}{RESET_FORMAT} | {footer2:^43} |
            """
        )[1:]
        print(menu, end="")
