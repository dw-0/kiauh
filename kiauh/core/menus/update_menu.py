# ======================================================================= #
#  Copyright (C) 2020 - 2024 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #

import textwrap

from components.klipper.klipper_setup import update_klipper
from components.klipper.klipper_utils import (
    get_klipper_status,
)
from components.moonraker.moonraker_setup import update_moonraker
from components.moonraker.moonraker_utils import get_moonraker_status
from components.webui_client.client_config.client_config_setup import (
    update_client_config,
)
from components.webui_client.client_setup import update_client
from components.webui_client.client_utils import (
    get_local_client_version,
    get_remote_client_version,
    get_client_config_status,
)
from components.webui_client.fluidd_data import FluiddData
from components.webui_client.mainsail_data import MainsailData
from core.menus.base_menu import BaseMenu
from utils.constants import (
    COLOR_GREEN,
    RESET_FORMAT,
    COLOR_YELLOW,
    COLOR_WHITE,
    COLOR_RED,
)


# noinspection PyUnusedLocal
# noinspection PyMethodMayBeStatic
class UpdateMenu(BaseMenu):
    def __init__(self, previous_menu):
        super().__init__()

        self.previous_menu: BaseMenu = previous_menu
        self.options = {
            "0": self.update_all,
            "1": self.update_klipper,
            "2": self.update_moonraker,
            "3": self.update_mainsail,
            "4": self.update_fluidd,
            "5": self.update_mainsail_config,
            "6": self.update_fluidd_config,
            "7": self.update_klipperscreen,
            "8": self.update_mobileraker,
            "9": self.update_crowsnest,
            "10": self.upgrade_system_packages,
        }

        self.kl_local = f"{COLOR_WHITE}{RESET_FORMAT}"
        self.kl_remote = f"{COLOR_WHITE}{RESET_FORMAT}"
        self.mr_local = f"{COLOR_WHITE}{RESET_FORMAT}"
        self.mr_remote = f"{COLOR_WHITE}{RESET_FORMAT}"
        self.ms_local = f"{COLOR_WHITE}{RESET_FORMAT}"
        self.ms_remote = f"{COLOR_WHITE}{RESET_FORMAT}"
        self.fl_local = f"{COLOR_WHITE}{RESET_FORMAT}"
        self.fl_remote = f"{COLOR_WHITE}{RESET_FORMAT}"
        self.mc_local = f"{COLOR_WHITE}{RESET_FORMAT}"
        self.mc_remote = f"{COLOR_WHITE}{RESET_FORMAT}"
        self.fc_local = f"{COLOR_WHITE}{RESET_FORMAT}"
        self.fc_remote = f"{COLOR_WHITE}{RESET_FORMAT}"

        self.mainsail_cient = MainsailData()
        self.fluidd_client = FluiddData()

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
            | Webinterface:         |---------------|---------------|
            |  3) Mainsail          | {self.ms_local:<22} | {self.ms_remote:<22} |
            |  4) Fluidd            | {self.fl_local:<22} | {self.fl_remote:<22} |
            |                       |               |               |
            | Client-Config:        |---------------|---------------|
            |  5) Mainsail-Config   | {self.mc_local:<22} | {self.mc_remote:<22} |
            |  6) Fluidd-Config     | {self.fc_local:<22} | {self.fc_remote:<22} |
            |                       |               |               |
            | Other:                |---------------|---------------|
            |  7) KlipperScreen     |               |               |
            |  8) Mobileraker       |               |               |
            |  9) Crowsnest         |               |               |
            |                       |-------------------------------|
            | 10) System            |                               |
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
        update_client(self.mainsail_cient)

    def update_mainsail_config(self, **kwargs):
        update_client_config(self.mainsail_cient)

    def update_fluidd(self, **kwargs):
        update_client(self.fluidd_client)

    def update_fluidd_config(self, **kwargs):
        update_client_config(self.fluidd_client)

    def update_klipperscreen(self, **kwargs): ...

    def update_mobileraker(self, **kwargs): ...

    def update_crowsnest(self, **kwargs): ...

    def upgrade_system_packages(self, **kwargs): ...

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
        self.ms_local = get_local_client_version(self.mainsail_cient)
        self.ms_remote = get_remote_client_version(self.mainsail_cient)
        if self.ms_local == self.ms_remote:
            self.ms_local = f"{COLOR_GREEN}{self.ms_local}{RESET_FORMAT}"
        else:
            self.ms_local = f"{COLOR_YELLOW}{self.ms_local}{RESET_FORMAT}"
        self.ms_remote = f"{COLOR_GREEN if self.ms_remote != 'ERROR' else COLOR_RED}{self.ms_remote}{RESET_FORMAT}"
        # fluidd
        self.fl_local = get_local_client_version(self.fluidd_client)
        self.fl_remote = get_remote_client_version(self.fluidd_client)
        if self.fl_local == self.fl_remote:
            self.fl_local = f"{COLOR_GREEN}{self.fl_local}{RESET_FORMAT}"
        else:
            self.fl_local = f"{COLOR_YELLOW}{self.fl_local}{RESET_FORMAT}"
        self.fl_remote = f"{COLOR_GREEN if self.fl_remote != 'ERROR' else COLOR_RED}{self.fl_remote}{RESET_FORMAT}"
        # mainsail-config
        mc_status = get_client_config_status(self.mainsail_cient)
        self.mc_local = mc_status.get("local")
        self.mc_remote = mc_status.get("remote")
        if self.mc_local == self.mc_remote:
            self.mc_local = f"{COLOR_GREEN}{self.mc_local}{RESET_FORMAT}"
        else:
            self.mc_local = f"{COLOR_YELLOW}{self.mc_local}{RESET_FORMAT}"
        self.mc_remote = f"{COLOR_GREEN}{self.mc_remote}{RESET_FORMAT}"
        # fluidd-config
        fc_status = get_client_config_status(self.fluidd_client)
        self.fc_local = fc_status.get("local")
        self.fc_remote = fc_status.get("remote")
        if self.fc_local == self.mc_remote:
            self.fc_local = f"{COLOR_GREEN}{self.fc_local}{RESET_FORMAT}"
        else:
            self.fc_local = f"{COLOR_YELLOW}{self.fc_local}{RESET_FORMAT}"
        self.fc_remote = f"{COLOR_GREEN}{self.fc_remote}{RESET_FORMAT}"
