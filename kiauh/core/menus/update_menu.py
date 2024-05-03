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
from components.klipperscreen.klipperscreen import (
    update_klipperscreen,
    get_klipperscreen_status,
)
from components.mobileraker.mobileraker import (
    update_mobileraker,
    get_mobileraker_status,
)
from components.moonraker.moonraker_setup import update_moonraker
from components.moonraker.moonraker_utils import get_moonraker_status
from components.webui_client.client_config.client_config_setup import (
    update_client_config,
)
from components.webui_client.client_setup import update_client
from components.webui_client.client_utils import (
    get_client_config_status,
    get_client_status,
)
from components.webui_client.fluidd_data import FluiddData
from components.webui_client.mainsail_data import MainsailData
from core.menus import Option
from core.menus.base_menu import BaseMenu
from utils.constants import (
    COLOR_GREEN,
    RESET_FORMAT,
    COLOR_YELLOW,
    COLOR_RED,
)


# noinspection PyUnusedLocal
# noinspection PyMethodMayBeStatic
class UpdateMenu(BaseMenu):
    def __init__(self, previous_menu: Optional[Type[BaseMenu]] = None):
        super().__init__()
        self.previous_menu = previous_menu

        self.kl_local = self.kl_remote = self.mr_local = self.mr_remote = ""
        self.ms_local = self.ms_remote = self.fl_local = self.fl_remote = ""
        self.mc_local = self.mc_remote = self.fc_local = self.fc_remote = ""
        self.ks_local = self.ks_remote = self.mb_local = self.mb_remote = ""
        self.cn_local = self.cn_remote = ""

        self.mainsail_data = MainsailData()
        self.fluidd_data = FluiddData()
        self._fetch_update_status()

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
        self._fetch_update_status()

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
            |  7) KlipperScreen     | {self.ks_local:<22} | {self.ks_remote:<22} |
            |  8) Mobileraker       | {self.mb_local:<22} | {self.mb_remote:<22} |
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
        update_client(self.mainsail_data)

    def update_mainsail_config(self, **kwargs):
        update_client_config(self.mainsail_data)

    def update_fluidd(self, **kwargs):
        update_client(self.fluidd_data)

    def update_fluidd_config(self, **kwargs):
        update_client_config(self.fluidd_data)

    def update_klipperscreen(self, **kwargs):
        update_klipperscreen()

    def update_mobileraker(self, **kwargs):
        update_mobileraker()

    def update_crowsnest(self, **kwargs):
        update_crowsnest()

    def upgrade_system_packages(self, **kwargs): ...

    def _fetch_update_status(self):
        # klipper
        self._get_update_status("kl", get_klipper_status)
        # moonraker
        self._get_update_status("mr", get_moonraker_status)
        # mainsail
        self._get_update_status("ms", get_client_status, self.mainsail_data, True)
        # mainsail-config
        self._get_update_status("mc", get_client_config_status, self.mainsail_data)
        # fluidd
        self._get_update_status("fl", get_client_status, self.fluidd_data, True)
        # fluidd-config
        self._get_update_status("fc", get_client_config_status, self.fluidd_data)
        # klipperscreen
        self._get_update_status("ks", get_klipperscreen_status)
        # mobileraker
        self._get_update_status("mb", get_mobileraker_status)
        # crowsnest
        self._get_update_status("cn", get_crowsnest_status)

    def _format_local_status(self, local_version, remote_version) -> str:
        if local_version == remote_version:
            return f"{COLOR_GREEN}{local_version}{RESET_FORMAT}"
        return f"{COLOR_YELLOW}{local_version}{RESET_FORMAT}"

    def _get_update_status(self, name: str, status_fn: callable, *args) -> None:
        status_data = status_fn(*args)
        local_ver = status_data.get("local")
        remote_ver = status_data.get("remote")
        color = COLOR_GREEN if remote_ver != "ERROR" else COLOR_RED
        setattr(self, f"{name}_local", self._format_local_status(local_ver, remote_ver))
        setattr(self, f"{name}_remote", f"{color}{remote_ver}{RESET_FORMAT}")
