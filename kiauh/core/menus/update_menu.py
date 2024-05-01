# ======================================================================= #
#  Copyright (C) 2020 - 2024 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #

import textwrap
from typing import Type, Optional

from components.crowsnest.crowsnest import get_crowsnest_status, update_crowsnest
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
from core.menus import Option
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
    def __init__(self, previous_menu: Optional[Type[BaseMenu]] = None):
        super().__init__()
        self.previous_menu = previous_menu

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
        self.cn_local = f"{COLOR_WHITE}{RESET_FORMAT}"
        self.cn_remote = f"{COLOR_WHITE}{RESET_FORMAT}"

        self.mainsail_client = MainsailData()
        self.fluidd_client = FluiddData()

    def set_previous_menu(self, previous_menu: Optional[Type[BaseMenu]]) -> None:
        from core.menus.main_menu import MainMenu

        self.previous_menu: Type[BaseMenu] = (
            previous_menu if previous_menu is not None else MainMenu
        )

    def set_options(self) -> None:
        self.options = {
            "0": Option(self.update_all, menu=False),
            "1": Option(self.update_klipper, menu=False),
            "2": Option(self.update_moonraker, menu=False),
            "3": Option(self.update_mainsail, menu=False),
            "4": Option(self.update_fluidd, menu=False),
            "5": Option(self.update_mainsail_config, menu=False),
            "6": Option(self.update_fluidd_config, menu=False),
            "7": Option(self.update_klipperscreen, menu=False),
            "8": Option(self.update_mobileraker, menu=False),
            "9": Option(self.update_crowsnest, menu=False),
            "10": Option(self.upgrade_system_packages, menu=False),
        }

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
            |  9) Crowsnest         | {self.cn_local:<22} | {self.cn_remote:<22} |
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
        update_client(self.mainsail_client)

    def update_mainsail_config(self, **kwargs):
        update_client_config(self.mainsail_client)

    def update_fluidd(self, **kwargs):
        update_client(self.fluidd_client)

    def update_fluidd_config(self, **kwargs):
        update_client_config(self.fluidd_client)

    def update_klipperscreen(self, **kwargs): ...

    def update_mobileraker(self, **kwargs): ...

    def update_crowsnest(self, **kwargs):
        update_crowsnest()

    def upgrade_system_packages(self, **kwargs): ...

    def fetch_update_status(self):
        # klipper
        kl_status = get_klipper_status()
        self.kl_local = self.format_local_status(
            kl_status.get("local"), kl_status.get("remote")
        )
        self.kl_remote = kl_status.get("remote")
        self.kl_remote = f"{COLOR_GREEN}{kl_status.get('remote')}{RESET_FORMAT}"

        # moonraker
        mr_status = get_moonraker_status()
        self.mr_local = self.format_local_status(
            mr_status.get("local"), mr_status.get("remote")
        )
        self.mr_remote = f"{COLOR_GREEN}{mr_status.get('remote')}{RESET_FORMAT}"

        # mainsail
        ms_local_ver = get_local_client_version(self.mainsail_client)
        ms_remote_ver = get_remote_client_version(self.mainsail_client)
        self.ms_local = self.format_local_status(ms_local_ver, ms_remote_ver)
        self.ms_remote = f"{COLOR_GREEN if ms_remote_ver != 'ERROR' else COLOR_RED}{ms_remote_ver}{RESET_FORMAT}"

        # fluidd
        fl_local_ver = get_local_client_version(self.fluidd_client)
        fl_remote_ver = get_remote_client_version(self.fluidd_client)
        self.fl_local = self.format_local_status(fl_local_ver, fl_remote_ver)
        self.fl_remote = f"{COLOR_GREEN if fl_remote_ver != 'ERROR' else COLOR_RED}{fl_remote_ver}{RESET_FORMAT}"

        # mainsail-config
        mc_status = get_client_config_status(self.mainsail_client)
        self.mc_local = self.format_local_status(
            mc_status.get("local"), mc_status.get("remote")
        )
        self.mc_remote = f"{COLOR_GREEN}{mc_status.get('remote')}{RESET_FORMAT}"

        # fluidd-config
        fc_status = get_client_config_status(self.fluidd_client)
        self.fc_local = self.format_local_status(
            fc_status.get("local"), fc_status.get("remote")
        )
        self.fc_remote = f"{COLOR_GREEN}{fc_status.get('remote')}{RESET_FORMAT}"

        # crowsnest
        cn_status = get_crowsnest_status()
        self.cn_local = self.format_local_status(
            cn_status.get("local"), cn_status.get("remote")
        )
        self.cn_remote = f"{COLOR_GREEN}{cn_status.get('remote')}{RESET_FORMAT}"

    def format_local_status(self, local_version, remote_version) -> str:
        if local_version == remote_version:
            return f"{COLOR_GREEN}{local_version}{RESET_FORMAT}"
        return f"{COLOR_YELLOW}{local_version}{RESET_FORMAT}"
