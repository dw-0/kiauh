# ======================================================================= #
#  Copyright (C) 2020 - 2024 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #
import sys
import textwrap
from typing import Optional, Type

from components.crowsnest.crowsnest import get_crowsnest_status
from components.klipper.klipper_utils import get_klipper_status
from components.klipperscreen.klipperscreen import get_klipperscreen_status
from components.log_uploads.menus.log_upload_menu import LogUploadMenu
from components.mobileraker.mobileraker import get_mobileraker_status
from components.moonraker.moonraker_utils import get_moonraker_status
from components.webui_client.client_utils import (
    get_client_status,
    get_current_client_config,
)
from components.webui_client.fluidd_data import FluiddData
from components.webui_client.mainsail_data import MainsailData
from core.menus import FooterType
from core.menus.advanced_menu import AdvancedMenu
from core.menus.backup_menu import BackupMenu
from core.menus.base_menu import BaseMenu, Option
from core.menus.install_menu import InstallMenu
from core.menus.remove_menu import RemoveMenu
from core.menus.settings_menu import SettingsMenu
from core.menus.update_menu import UpdateMenu
from extensions.extensions_menu import ExtensionsMenu
from utils.constants import (
    COLOR_CYAN,
    COLOR_GREEN,
    COLOR_MAGENTA,
    COLOR_RED,
    COLOR_YELLOW,
    RESET_FORMAT,
)
from utils.logger import Logger
from utils.types import ComponentStatus


# noinspection PyUnusedLocal
# noinspection PyMethodMayBeStatic
class MainMenu(BaseMenu):
    def __init__(self):
        super().__init__()

        self.header = True
        self.footer_type = FooterType.QUIT

        self.kl_status = self.kl_repo = self.mr_status = self.mr_repo = ""
        self.ms_status = self.fl_status = self.ks_status = self.mb_status = ""
        self.cn_status = self.cc_status = ""
        self.init_status()

    def set_previous_menu(self, previous_menu: Optional[Type[BaseMenu]]) -> None:
        """MainMenu does not have a previous menu"""
        pass

    def set_options(self) -> None:
        self.options = {
            "0": Option(method=self.log_upload_menu, menu=True),
            "1": Option(method=self.install_menu, menu=True),
            "2": Option(method=self.update_menu, menu=True),
            "3": Option(method=self.remove_menu, menu=True),
            "4": Option(method=self.advanced_menu, menu=True),
            "5": Option(method=self.backup_menu, menu=True),
            "e": Option(method=self.extension_menu, menu=True),
            "s": Option(method=self.settings_menu, menu=True),
        }

    def init_status(self) -> None:
        status_vars = ["kl", "mr", "ms", "fl", "ks", "mb", "cn"]
        for var in status_vars:
            setattr(
                self,
                f"{var}_status",
                f"{COLOR_RED}Not installed!{RESET_FORMAT}",
            )

    def fetch_status(self) -> None:
        self._get_component_status("kl", get_klipper_status)
        self._get_component_status("mr", get_moonraker_status)
        self._get_component_status("ms", get_client_status, MainsailData())
        self._get_component_status("fl", get_client_status, FluiddData())
        self.cc_status = get_current_client_config([MainsailData(), FluiddData()])
        self._get_component_status("ks", get_klipperscreen_status)
        self._get_component_status("mb", get_mobileraker_status)
        self._get_component_status("cn", get_crowsnest_status)

    def _get_component_status(self, name: str, status_fn: callable, *args) -> None:
        status_data: ComponentStatus = status_fn(*args)
        code: int = status_data.get("status").value.code
        status: str = status_data.get("status").value.txt
        repo: str = status_data.get("repo")
        instance_count: int = status_data.get("instances")

        count_txt: str = ""
        if instance_count > 0 and code == 1:
            count_txt = f": {instance_count}"

        setattr(self, f"{name}_status", self._format_by_code(code, status, count_txt))
        setattr(self, f"{name}_repo", f"{COLOR_CYAN}{repo}{RESET_FORMAT}")

    def _format_by_code(self, code: int, status: str, count: str) -> str:
        if code == 1:
            return f"{COLOR_GREEN}{status}{count}{RESET_FORMAT}"
        elif code == 2:
            return f"{COLOR_RED}{status}{count}{RESET_FORMAT}"

        return f"{COLOR_YELLOW}{status}{count}{RESET_FORMAT}"

    def print_menu(self):
        self.fetch_status()

        header = " [ Main Menu ] "
        footer1 = f"{COLOR_CYAN}KIAUH v6.0.0{RESET_FORMAT}"
        footer2 = f"Changelog: {COLOR_MAGENTA}https://git.io/JnmlX{RESET_FORMAT}"
        color = COLOR_CYAN
        count = 62 - len(color) - len(RESET_FORMAT)
        pad1 = 32
        pad2 = 26
        menu = textwrap.dedent(
            f"""
            ╔═══════════════════════════════════════════════════════╗
            ║ {color}{header:~^{count}}{RESET_FORMAT} ║
            ╟──────────────────┬────────────────────────────────────╢
            ║  0) [Log-Upload] │   Klipper: {self.kl_status:<{pad1}} ║
            ║                  │      Repo: {self.kl_repo:<{pad1}} ║
            ║  1) [Install]    ├────────────────────────────────────╢
            ║  2) [Update]     │ Moonraker: {self.mr_status:<{pad1}} ║
            ║  3) [Remove]     │      Repo: {self.mr_repo:<{pad1}} ║
            ║  4) [Advanced]   ├────────────────────────────────────╢
            ║  5) [Backup]     │        Mainsail: {self.ms_status:<{pad2}} ║
            ║                  │          Fluidd: {self.fl_status:<{pad2}} ║
            ║  S) [Settings]   │   Client-Config: {self.cc_status:<{pad2}} ║
            ║                  │                                    ║
            ║ Community:       │   KlipperScreen: {self.ks_status:<{pad2}} ║
            ║  E) [Extensions] │     Mobileraker: {self.mb_status:<{pad2}} ║
            ║                  │       Crowsnest: {self.cn_status:<{pad2}} ║
            ╟──────────────────┼────────────────────────────────────╢
            ║ {footer1:^25} │ {footer2:^43} ║
            ╟──────────────────┴────────────────────────────────────╢
            """
        )[1:]
        print(menu, end="")

    def exit(self, **kwargs):
        Logger.print_ok("###### Happy printing!", False)
        sys.exit(0)

    def log_upload_menu(self, **kwargs):
        LogUploadMenu().run()

    def install_menu(self, **kwargs):
        InstallMenu(previous_menu=self.__class__).run()

    def update_menu(self, **kwargs):
        UpdateMenu(previous_menu=self.__class__).run()

    def remove_menu(self, **kwargs):
        RemoveMenu(previous_menu=self.__class__).run()

    def advanced_menu(self, **kwargs):
        AdvancedMenu(previous_menu=self.__class__).run()

    def backup_menu(self, **kwargs):
        BackupMenu(previous_menu=self.__class__).run()

    def settings_menu(self, **kwargs):
        SettingsMenu(previous_menu=self.__class__).run()

    def extension_menu(self, **kwargs):
        ExtensionsMenu(previous_menu=self.__class__).run()
