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

from kiauh.components.klipper.klipper_utils import backup_klipper_dir
from kiauh.components.mainsail.mainsail_utils import backup_mainsail_data
from kiauh.components.moonraker.moonraker_utils import (
    backup_moonraker_dir,
    backup_moonraker_db_dir,
)
from kiauh.core.menus import BACK_FOOTER
from kiauh.core.menus.base_menu import BaseMenu
from kiauh.utils.common import backup_printer_config_dir
from kiauh.utils.constants import COLOR_CYAN, RESET_FORMAT, COLOR_YELLOW


# noinspection PyUnusedLocal
# noinspection PyMethodMayBeStatic
class BackupMenu(BaseMenu):
    def __init__(self):
        super().__init__(
            header=True,
            options={
                "1": self.backup_klipper,
                "2": self.backup_moonraker,
                "3": self.backup_printer_config,
                "4": self.backup_moonraker_db,
                "5": self.backup_mainsail,
            },
            footer_type=BACK_FOOTER,
        )

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
            | Klipper & Moonraker API:   | Touchscreen GUI:         |
            |  1) [Klipper]              |  7) [KlipperScreen]      |
            |  2) [Moonraker]            |                          |
            |  3) [Config Folder]        | Other:                   |
            |  4) [Moonraker Database]   |  9) [Telegram Bot]       |
            |                            |                          |
            | Klipper Webinterface:      |                          |
            |  5) [Mainsail]             |                          |
            |  6) [Fluidd]               |                          |
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
        backup_mainsail_data()

    def backup_fluidd(self, **kwargs):
        pass

    def backup_klipperscreen(self, **kwargs):
        pass

    def backup_telegram_bot(self, **kwargs):
        pass
