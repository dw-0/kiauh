# ======================================================================= #
#  Copyright (C) 2020 - 2024 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #
from __future__ import annotations

import textwrap
from typing import Type

from components.webui_client.base_data import BaseWebClient
from components.webui_client.client_setup import install_client
from components.webui_client.client_utils import (
    get_client_port_selection,
    set_listen_port,
)
from core.constants import COLOR_CYAN, COLOR_GREEN, RESET_FORMAT
from core.logger import DialogCustomColor, DialogType, Logger
from core.menus import Option
from core.menus.base_menu import BaseMenu
from core.settings.kiauh_settings import KiauhSettings, WebUiSettings
from utils.sys_utils import cmd_sysctl_service, get_ipv4_addr


# noinspection PyUnusedLocal
class ClientInstallMenu(BaseMenu):
    def __init__(
        self, client: BaseWebClient, previous_menu: Type[BaseMenu] | None = None
    ):
        super().__init__()
        self.previous_menu: Type[BaseMenu] | None = previous_menu
        self.client: BaseWebClient = client
        self.settings = KiauhSettings()
        self.client_settings: WebUiSettings = self.settings[client.name]

    def set_previous_menu(self, previous_menu: Type[BaseMenu] | None) -> None:
        from core.menus.install_menu import InstallMenu

        self.previous_menu = previous_menu if previous_menu is not None else InstallMenu

    def set_options(self) -> None:
        self.options = {
            "1": Option(method=self.reinstall_client),
            "2": Option(method=self.change_listen_port),
        }

    def print_menu(self) -> None:
        client_name = self.client.display_name

        header = f" [ Installation Menu > {client_name} ] "
        color = COLOR_GREEN
        count = 62 - len(color) - len(RESET_FORMAT)
        port = f"(Current: {COLOR_CYAN}{int(self.client_settings.port)}{RESET_FORMAT})"
        menu = textwrap.dedent(
            f"""
            ╔═══════════════════════════════════════════════════════╗
            ║ {color}{header:~^{count}}{RESET_FORMAT} ║
            ╟───────────────────────────────────────────────────────╢
            ║  1) Reinstall {client_name:16}                        ║
            ║  2) Reconfigure Listen Port {port:<34} ║
            ╟───────────────────────────────────────────────────────╢
            """
        )[1:]
        print(menu, end="")

    def reinstall_client(self, **kwargs) -> None:
        install_client(self.client, settings=self.settings, reinstall=True)

    def change_listen_port(self, **kwargs) -> None:
        curr_port = int(self.client_settings.port)
        new_port = get_client_port_selection(
            self.client,
            self.settings,
            reconfigure=True,
        )

        cmd_sysctl_service("nginx", "stop")
        set_listen_port(self.client, curr_port, new_port)

        Logger.print_status("Saving new port configuration ...")
        self.client_settings.port = new_port
        self.settings.save()
        Logger.print_ok("Port configuration saved!")

        cmd_sysctl_service("nginx", "start")

        # noinspection HttpUrlsUsage
        Logger.print_dialog(
            DialogType.CUSTOM,
            custom_title="Port reconfiguration complete!",
            custom_color=DialogCustomColor.GREEN,
            center_content=True,
            content=[
                f"Open {self.client.display_name} now on: "
                f"http://{get_ipv4_addr()}:{new_port}",
            ],
        )

    def _go_back(self, **kwargs) -> None:
        if self.previous_menu is not None:
            self.previous_menu().run()
