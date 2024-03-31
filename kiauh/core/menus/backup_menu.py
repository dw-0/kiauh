# ======================================================================= #
#  Copyright (C) 2020 - 2024 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #

import textwrap

from components.klipper.klipper_utils import backup_klipper_dir
from components.moonraker.moonraker_utils import (
    backup_moonraker_dir,
    backup_moonraker_db_dir,
)
from components.webui_client.client_utils import (
    backup_client_data,
    load_client_data,
    backup_client_config_data,
)
from core.menus.base_menu import BaseMenu
from utils.common import backup_printer_config_dir
from utils.constants import COLOR_CYAN, RESET_FORMAT, COLOR_YELLOW


# noinspection PyUnusedLocal
# noinspection PyMethodMayBeStatic
class BackupMenu(BaseMenu):
    def __init__(self, previous_menu: BaseMenu):
        super().__init__()

        self.previous_menu: BaseMenu = previous_menu
        self.options = {
            "1": self.backup_klipper,
            "2": self.backup_moonraker,
            "3": self.backup_printer_config,
            "4": self.backup_moonraker_db,
            "5": self.backup_mainsail,
            "6": self.backup_fluidd,
            "7": self.backup_mainsail_config,
            "8": self.backup_fluidd_config,
            "9": self.backup_klipperscreen,
        }

    def print_menu(self):
        header = " [ Backup Menu ] "
        line1 = f"{COLOR_YELLOW}INFO: Backups are located in '~/kiauh-backups'{RESET_FORMAT}"
        color = COLOR_CYAN
        count = 62 - len(color) - len(RESET_FORMAT)
        menu = textwrap.dedent(
            f"""
            /=======================================================\\
            | {color}{header:~^{count}}{RESET_FORMAT} |
            |-------------------------------------------------------|
            | {line1:^62} |
            |-------------------------------------------------------|
            | Klipper & Moonraker API:  | Client-Config:            |
            |  1) [Klipper]             |  7) [Mainsail-Config]     |
            |  2) [Moonraker]           |  8) [Fluidd-Config]       |
            |  3) [Config Folder]       |                           |
            |  4) [Moonraker Database]  | Touchscreen GUI:          |
            |                           |  9) [KlipperScreen]       |
            | Webinterface:             |                           |
            |  5) [Mainsail]            |                           |
            |  6) [Fluidd]              |                           |
            """
        )[1:]
        print(menu, end="")

    def backup_klipper(self, **kwargs):
        backup_klipper_dir()

    def backup_moonraker(self, **kwargs):
        backup_moonraker_dir()

    def backup_printer_config(self, **kwargs):
        backup_printer_config_dir()

    def backup_moonraker_db(self, **kwargs):
        backup_moonraker_db_dir()

    def backup_mainsail(self, **kwargs):
        backup_client_data(load_client_data("mainsail"))

    def backup_fluidd(self, **kwargs):
        backup_client_data(load_client_data("fluidd"))

    def backup_mainsail_config(self, **kwargs):
        backup_client_config_data(load_client_data("mainsail"))

    def backup_fluidd_config(self, **kwargs):
        backup_client_config_data(load_client_data("fluidd"))

    def backup_klipperscreen(self, **kwargs):
        pass
