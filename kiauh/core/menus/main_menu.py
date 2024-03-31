# ======================================================================= #
#  Copyright (C) 2020 - 2024 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #

import textwrap

from components.klipper.klipper_utils import get_klipper_status
from components.log_uploads.menus.log_upload_menu import LogUploadMenu
from components.moonraker.moonraker_utils import get_moonraker_status
from components.webui_client.client_utils import (
    get_client_status,
    load_client_data,
    get_current_client_config,
)
from core.menus import FooterType
from core.menus.advanced_menu import AdvancedMenu
from core.menus.backup_menu import BackupMenu
from core.menus.base_menu import BaseMenu
from core.menus.extensions_menu import ExtensionsMenu
from core.menus.install_menu import InstallMenu
from core.menus.remove_menu import RemoveMenu
from core.menus.settings_menu import SettingsMenu
from core.menus.update_menu import UpdateMenu
from utils.constants import (
    COLOR_MAGENTA,
    COLOR_CYAN,
    RESET_FORMAT,
    COLOR_RED,
    COLOR_GREEN,
    COLOR_YELLOW,
)


# noinspection PyMethodMayBeStatic
class MainMenu(BaseMenu):
    def __init__(self):
        super().__init__()

        self.options = {
            "0": lambda: LogUploadMenu(previous_menu=self).run(),
            "1": lambda: InstallMenu(previous_menu=self).run(),
            "2": lambda: UpdateMenu(previous_menu=self).run(),
            "3": lambda: RemoveMenu(previous_menu=self).run(),
            "4": lambda: AdvancedMenu(previous_menu=self).run(),
            "5": lambda: BackupMenu(previous_menu=self).run(),
            "6": None,
            "e": lambda: ExtensionsMenu(previous_menu=self).run(),
            "s": lambda: SettingsMenu(previous_menu=self).run(),
        }
        self.header = True
        self.footer_type = FooterType.QUIT

        self.kl_status = ""
        self.kl_repo = ""
        self.mr_status = ""
        self.mr_repo = ""
        self.ms_status = ""
        self.fl_status = ""
        self.ks_status = ""
        self.mb_status = ""
        self.cn_status = ""
        self.cc_status = ""
        self.init_status()

    def init_status(self) -> None:
        status_vars = ["kl", "mr", "ms", "fl", "ks", "mb", "cn"]
        for var in status_vars:
            setattr(
                self,
                f"{var}_status",
                f"{COLOR_RED}Not installed!{RESET_FORMAT}",
            )

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
        mainsail_client_data = load_client_data("mainsail")
        self.ms_status = get_client_status(mainsail_client_data)
        # fluidd
        fluidd_client_data = load_client_data("fluidd")
        self.fl_status = get_client_status(fluidd_client_data)
        # client-config
        self.cc_status = get_current_client_config(
            [mainsail_client_data, fluidd_client_data]
        )

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
            |  S) [Settings]   |   Client-Config: {self.cc_status:<26} |
            |                  |                                    |
            | Community:       |   KlipperScreen: {self.ks_status:<26} |
            |  E) [Extensions] |     Mobileraker: {self.mb_status:<26} |
            |                  |       Crowsnest: {self.cn_status:<26} |
            |-------------------------------------------------------|
            | {COLOR_CYAN}{footer1:^16}{RESET_FORMAT} | {footer2:^43} |
            """
        )[1:]
        print(menu, end="")
