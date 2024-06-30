# ======================================================================= #
#  Copyright (C) 2020 - 2024 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #
import textwrap
from typing import Optional, Type

from components.crowsnest.crowsnest import get_crowsnest_status, update_crowsnest
from components.klipper.klipper_setup import update_klipper
from components.klipper.klipper_utils import (
    get_klipper_status,
)
from components.klipperscreen.klipperscreen import (
    get_klipperscreen_status,
    update_klipperscreen,
)
from components.mobileraker.mobileraker import (
    get_mobileraker_status,
    update_mobileraker,
)
from components.moonraker.moonraker_setup import update_moonraker
from components.moonraker.moonraker_utils import get_moonraker_status
from components.octoeverywhere.octoeverywhere_setup import (
    get_octoeverywhere_status,
    update_octoeverywhere,
)
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
    COLOR_RED,
    COLOR_YELLOW,
    RESET_FORMAT,
)
from utils.logger import Logger
from utils.spinner import Spinner
from utils.types import ComponentStatus


# noinspection PyUnusedLocal
# noinspection PyMethodMayBeStatic
class UpdateMenu(BaseMenu):
    def __init__(self, previous_menu: Optional[Type[BaseMenu]] = None):
        super().__init__()
        self.previous_menu = previous_menu

        self.klipper_local = self.klipper_remote = ""
        self.moonraker_local = self.moonraker_remote = ""
        self.mainsail_local = self.mainsail_remote = ""
        self.mainsail_config_local = self.mainsail_config_remote = ""
        self.fluidd_local = self.fluidd_remote = ""
        self.fluidd_config_local = self.fluidd_config_remote = ""
        self.klipperscreen_local = self.klipperscreen_remote = ""
        self.mobileraker_local = self.mobileraker_remote = ""
        self.crowsnest_local = self.crowsnest_remote = ""
        self.octoeverywhere_local = self.octoeverywhere_remote = ""

        self.mainsail_data = MainsailData()
        self.fluidd_data = FluiddData()
        self.status_data = {
            "klipper": {"installed": False, "local": None, "remote": None},
            "moonraker": {"installed": False, "local": None, "remote": None},
            "mainsail": {"installed": False, "local": None, "remote": None},
            "mainsail_config": {"installed": False, "local": None, "remote": None},
            "fluidd": {"installed": False, "local": None, "remote": None},
            "fluidd_config": {"installed": False, "local": None, "remote": None},
            "mobileraker": {"installed": False, "local": None, "remote": None},
            "klipperscreen": {"installed": False, "local": None, "remote": None},
            "crowsnest": {"installed": False, "local": None, "remote": None},
            "octoeverywhere": {"installed": False, "local": None, "remote": None},
        }

    def set_previous_menu(self, previous_menu: Optional[Type[BaseMenu]]) -> None:
        from core.menus.main_menu import MainMenu

        self.previous_menu: Type[BaseMenu] = (
            previous_menu if previous_menu is not None else MainMenu
        )

    def set_options(self) -> None:
        self.options = {
            "a": Option(self.update_all, menu=False),
            "1": Option(self.update_klipper, menu=False),
            "2": Option(self.update_moonraker, menu=False),
            "3": Option(self.update_mainsail, menu=False),
            "4": Option(self.update_fluidd, menu=False),
            "5": Option(self.update_mainsail_config, menu=False),
            "6": Option(self.update_fluidd_config, menu=False),
            "7": Option(self.update_klipperscreen, menu=False),
            "8": Option(self.update_mobileraker, menu=False),
            "9": Option(self.update_crowsnest, menu=False),
            "10": Option(self.update_octoeverywhere, menu=False),
            "11": Option(self.upgrade_system_packages, menu=False),
        }

    def print_menu(self):
        spinner = Spinner()
        spinner.start()

        self._fetch_update_status()

        spinner.stop()

        header = " [ Update Menu ] "
        color = COLOR_GREEN
        count = 62 - len(color) - len(RESET_FORMAT)
        menu = textwrap.dedent(
            f"""
            ╔═══════════════════════════════════════════════════════╗
            ║ {color}{header:~^{count}}{RESET_FORMAT} ║
            ╟───────────────────────┬───────────────┬───────────────╢
            ║  a) Update all        │               │               ║
            ║                       │ Current:      │ Latest:       ║
            ║ Klipper & API:        ├───────────────┼───────────────╢
            ║  1) Klipper           │ {self.klipper_local:<22} │ {self.klipper_remote:<22} ║
            ║  2) Moonraker         │ {self.moonraker_local:<22} │ {self.moonraker_remote:<22} ║
            ║                       │               │               ║
            ║ Webinterface:         ├───────────────┼───────────────╢
            ║  3) Mainsail          │ {self.mainsail_local:<22} │ {self.mainsail_remote:<22} ║
            ║  4) Fluidd            │ {self.fluidd_local:<22} │ {self.fluidd_remote:<22} ║
            ║                       │               │               ║
            ║ Client-Config:        ├───────────────┼───────────────╢
            ║  5) Mainsail-Config   │ {self.mainsail_config_local:<22} │ {self.mainsail_config_remote:<22} ║
            ║  6) Fluidd-Config     │ {self.fluidd_config_local:<22} │ {self.fluidd_config_remote:<22} ║
            ║                       │               │               ║
            ║ Other:                ├───────────────┼───────────────╢
            ║  7) KlipperScreen     │ {self.klipperscreen_local:<22} │ {self.klipperscreen_remote:<22} ║
            ║  8) Mobileraker       │ {self.mobileraker_local:<22} │ {self.mobileraker_remote:<22} ║
            ║  9) Crowsnest         │ {self.crowsnest_local:<22} │ {self.crowsnest_remote:<22} ║
            ║ 10) OctoEverywhere    │ {self.octoeverywhere_local:<22} │ {self.octoeverywhere_remote:<22} ║
            ║                       ├───────────────┴───────────────╢
            ║ 11) System            │                               ║
            ╟───────────────────────┴───────────────────────────────╢
            """
        )[1:]
        print(menu, end="")

    def update_all(self, **kwargs):
        print("update_all")

    def update_klipper(self, **kwargs):
        if self._check_is_installed("klipper"):
            update_klipper()

    def update_moonraker(self, **kwargs):
        if self._check_is_installed("moonraker"):
            update_moonraker()

    def update_mainsail(self, **kwargs):
        if self._check_is_installed("mainsail"):
            update_client(self.mainsail_data)

    def update_mainsail_config(self, **kwargs):
        if self._check_is_installed("mainsail_config"):
            update_client_config(self.mainsail_data)

    def update_fluidd(self, **kwargs):
        if self._check_is_installed("fluidd"):
            update_client(self.fluidd_data)

    def update_fluidd_config(self, **kwargs):
        if self._check_is_installed("fluidd_config"):
            update_client_config(self.fluidd_data)

    def update_klipperscreen(self, **kwargs):
        if self._check_is_installed("klipperscreen"):
            update_klipperscreen()

    def update_mobileraker(self, **kwargs):
        if self._check_is_installed("mobileraker"):
            update_mobileraker()

    def update_crowsnest(self, **kwargs):
        if self._check_is_installed("crowsnest"):
            update_crowsnest()

    def update_octoeverywhere(self, **kwargs):
        if self._check_is_installed("octoeverywhere"):
            update_octoeverywhere()

    def upgrade_system_packages(self, **kwargs): ...

    def _fetch_update_status(self):
        self._set_status_data("klipper", get_klipper_status)
        self._set_status_data("moonraker", get_moonraker_status)
        self._set_status_data("mainsail", get_client_status, self.mainsail_data, True)
        self._set_status_data(
            "mainsail_config", get_client_config_status, self.mainsail_data
        )
        self._set_status_data("fluidd", get_client_status, self.fluidd_data, True)
        self._set_status_data(
            "fluidd_config", get_client_config_status, self.fluidd_data
        )
        self._set_status_data("klipperscreen", get_klipperscreen_status)
        self._set_status_data("mobileraker", get_mobileraker_status)
        self._set_status_data("crowsnest", get_crowsnest_status)
        self._set_status_data("octoeverywhere", get_octoeverywhere_status)

    def _format_local_status(self, local_version, remote_version) -> str:
        color = COLOR_RED
        if not local_version:
            color = COLOR_RED
        elif local_version == remote_version:
            color = COLOR_GREEN
        elif local_version != remote_version:
            color = COLOR_YELLOW

        return f"{color}{local_version or '-'}{RESET_FORMAT}"

    def _set_status_data(self, name: str, status_fn: callable, *args) -> None:
        comp_status: ComponentStatus = status_fn(*args)

        self.status_data[name]["installed"] = True if comp_status.status == 2 else False
        self.status_data[name]["local"] = comp_status.local
        self.status_data[name]["remote"] = comp_status.remote

        self._set_status_string(name)

    def _set_status_string(self, name: str) -> None:
        local_status = self.status_data[name].get("local", None)
        remote_status = self.status_data[name].get("remote", None)

        color = COLOR_GREEN if remote_status else COLOR_RED
        local_txt = self._format_local_status(local_status, remote_status)
        remote_txt = f"{color}{remote_status or '-'}{RESET_FORMAT}"

        setattr(self, f"{name}_local", local_txt)
        setattr(self, f"{name}_remote", remote_txt)

    def _check_is_installed(self, name: str) -> bool:
        if not self.status_data[name]["installed"]:
            Logger.print_info(f"{name.capitalize()} is not installed! Skipped ...")
            return False
        return True
