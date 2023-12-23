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
from kiauh.modules.klipper import KLIPPER_DIR, KLIPPER_ENV_DIR
from kiauh.modules.klipper.klipper import Klipper
from kiauh.modules.moonraker import MOONRAKER_DIR, MOONRAKER_ENV_DIR
from kiauh.modules.moonraker.moonraker import Moonraker
from kiauh.utils.common import get_repo_name, get_install_status_common
from kiauh.utils.constants import COLOR_MAGENTA, COLOR_CYAN, RESET_FORMAT, COLOR_RED


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
        self.kl_status = None
        self.kl_repo = None
        self.mr_status = None
        self.mr_repo = None
        self.ms_status = None
        self.fl_status = None
        self.ks_status = None
        self.mb_status = None
        self.cn_status = None
        self.tg_status = None
        self.ob_status = None
        self.oe_status = None
        self.init_status()

    def init_status(self) -> None:
        status_vars = ["kl", "mr", "ms", "fl", "ks", "mb", "cn", "tg", "ob", "oe"]
        for var in status_vars:
            setattr(self, f"{var}_status", f"{COLOR_RED}Not installed!{RESET_FORMAT}")

    def fetch_status(self) -> None:
        # klipper
        self.kl_status = get_install_status_common(
            Klipper, KLIPPER_DIR, KLIPPER_ENV_DIR
        )
        self.kl_repo = get_repo_name(KLIPPER_DIR)
        # moonraker
        self.mr_status = get_install_status_common(
            Moonraker, MOONRAKER_DIR, MOONRAKER_ENV_DIR
        )
        self.mr_repo = get_repo_name(MOONRAKER_DIR)

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
