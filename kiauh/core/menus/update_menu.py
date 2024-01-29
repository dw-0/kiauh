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

from kiauh.core.menus import BACK_FOOTER
from kiauh.core.menus.base_menu import BaseMenu
from kiauh.components.klipper.klipper_setup import update_klipper
from kiauh.components.klipper.klipper_utils import (
    get_klipper_status,
)
from kiauh.components.mainsail.mainsail_setup import update_mainsail
from kiauh.components.mainsail.mainsail_utils import (
    get_mainsail_local_version,
    get_mainsail_remote_version,
)
from kiauh.components.moonraker.moonraker_setup import update_moonraker
from kiauh.components.moonraker.moonraker_utils import get_moonraker_status
from kiauh.utils.constants import COLOR_GREEN, RESET_FORMAT, COLOR_YELLOW, COLOR_WHITE


# noinspection PyUnusedLocal
# noinspection PyMethodMayBeStatic
class UpdateMenu(BaseMenu):
    def __init__(self):
        super().__init__(
            header=True,
            options={
                0: self.update_all,
                1: self.update_klipper,
                2: self.update_moonraker,
                3: self.update_mainsail,
                4: self.update_fluidd,
                5: self.update_klipperscreen,
                6: self.update_pgc_for_klipper,
                7: self.update_telegram_bot,
                8: self.update_moonraker_obico,
                9: self.update_octoeverywhere,
                10: self.update_mobileraker,
                11: self.update_crowsnest,
                12: self.upgrade_system_packages,
            },
            footer_type=BACK_FOOTER,
        )
        self.kl_local = f"{COLOR_WHITE}{RESET_FORMAT}"
        self.kl_remote = f"{COLOR_WHITE}{RESET_FORMAT}"
        self.mr_local = f"{COLOR_WHITE}{RESET_FORMAT}"
        self.mr_remote = f"{COLOR_WHITE}{RESET_FORMAT}"
        self.ms_local = f"{COLOR_WHITE}{RESET_FORMAT}"
        self.ms_remote = f"{COLOR_WHITE}{RESET_FORMAT}"

    def print_menu(self):
        self.fetch_update_status()

        header = " [ Update Menu ] "
        color = COLOR_GREEN
        count = 62 - len(color) - len(RESET_FORMAT)
        menu = textwrap.dedent(
            f"""
            /=======================================================\\
            | {color}{header:~^{count}}{RESET_FORMAT} |
            |-------------------------------------------------------|
            |  0) Update all        |               |               |
            |                       | Current:      | Latest:       |
            | Klipper & API:        |---------------|---------------|
            |  1) Klipper           | {self.kl_local:<22} | {self.kl_remote:<22} |
            |  2) Moonraker         | {self.mr_local:<22} | {self.mr_remote:<22} |
            |                       |               |               |
            | Klipper Webinterface: |---------------|---------------|
            |  3) Mainsail          | {self.ms_local:<22} | {self.ms_remote:<22} |
            |  4) Fluidd            |               |               |
            |                       |               |               |
            | Touchscreen GUI:      |---------------|---------------|
            |  5) KlipperScreen     |               |               |
            |                       |               |               |
            | Other:                |---------------|---------------|
            |  6) PrettyGCode       |               |               |
            |  7) Telegram Bot      |               |               |
            |  8) Obico for Klipper |               |               |
            |  9) OctoEverywhere    |               |               |
            | 10) Mobileraker       |               |               |
            | 11) Crowsnest         |               |               |
            |                       |-------------------------------|
            | 12) System            |                               |
            """
        )[1:]
        print(menu, end="")

    def update_all(self, **kwargs):
        print("update_all")

    def update_klipper(self, **kwargs):
        update_klipper()

    def update_moonraker(self, **kwargs):
        update_moonraker()

    def update_mainsail(self, **kwargs):
        update_mainsail()

    def update_fluidd(self, **kwargs):
        print("update_fluidd")

    def update_klipperscreen(self, **kwargs):
        print("update_klipperscreen")

    def update_pgc_for_klipper(self, **kwargs):
        print("update_pgc_for_klipper")

    def update_telegram_bot(self, **kwargs):
        print("update_telegram_bot")

    def update_moonraker_obico(self, **kwargs):
        print("update_moonraker_obico")

    def update_octoeverywhere(self, **kwargs):
        print("update_octoeverywhere")

    def update_mobileraker(self, **kwargs):
        print("update_mobileraker")

    def update_crowsnest(self, **kwargs):
        print("update_crowsnest")

    def upgrade_system_packages(self, **kwargs):
        print("upgrade_system_packages")

    def fetch_update_status(self):
        # klipper
        kl_status = get_klipper_status()
        self.kl_local = kl_status.get("local")
        self.kl_remote = kl_status.get("remote")
        if self.kl_local == self.kl_remote:
            self.kl_local = f"{COLOR_GREEN}{self.kl_local}{RESET_FORMAT}"
        else:
            self.kl_local = f"{COLOR_YELLOW}{self.kl_local}{RESET_FORMAT}"
        self.kl_remote = f"{COLOR_GREEN}{self.kl_remote}{RESET_FORMAT}"
        # moonraker
        mr_status = get_moonraker_status()
        self.mr_local = mr_status.get("local")
        self.mr_remote = mr_status.get("remote")
        if self.mr_local == self.mr_remote:
            self.mr_local = f"{COLOR_GREEN}{self.mr_local}{RESET_FORMAT}"
        else:
            self.mr_local = f"{COLOR_YELLOW}{self.mr_local}{RESET_FORMAT}"
        self.mr_remote = f"{COLOR_GREEN}{self.mr_remote}{RESET_FORMAT}"
        # mainsail
        self.ms_local = get_mainsail_local_version()
        self.ms_remote = get_mainsail_remote_version()
        if self.ms_local == self.ms_remote:
            self.ms_local = f"{COLOR_GREEN}{self.ms_local}{RESET_FORMAT}"
        else:
            self.ms_local = f"{COLOR_YELLOW}{self.ms_local}{RESET_FORMAT}"
        self.ms_remote = f"{COLOR_GREEN}{self.ms_remote}{RESET_FORMAT}"
