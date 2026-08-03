# ======================================================================= #
#  Copyright (C) 2020 - 2026 Dominik Willner <dev.dw-0@proton.me>         #
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
from components.webui_client.client_utils import (
    get_client_port_selection,
    get_nginx_listen_port,
    set_listen_port,
)
from components.webui_client.services.web_client_setup_service import (
    WebClientSetupService,
)
from core.i18n import _tr
from core.logger import Logger
from core.menus import Option
from core.menus.base_menu import BaseMenu
from core.services.message_service import Message
from core.settings.kiauh_settings import KiauhSettings, WebUiSettings
from core.types.color import Color
from utils.sys_utils import cmd_sysctl_service, get_ipv4_addr


# noinspection PyUnusedLocal
class ClientInstallMenu(BaseMenu):
    def __init__(
        self, client: BaseWebClient, previous_menu: Type[BaseMenu] | None = None
    ):
        super().__init__()
        self.title = _tr("Installation Menu > {}").format(client.display_name)
        self.title_color = Color.GREEN
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
        port = _tr("(Current: {})").format(Color.apply(self._get_current_port(), Color.GREEN))
        menu = textwrap.dedent(
            f"""
            ╟───────────────────────────────────────────────────────╢
            ║  1) Reinstall {client_name:16}                        ║
            ║  2) Reconfigure Listen Port {port:<34} ║
            ╟───────────────────────────────────────────────────────╢
            """
        )[1:]
        print(menu, end="")

    def reinstall_client(self, **kwargs) -> None:
        WebClientSetupService(self.client.name).install(
            reinstall=True, interactive=True
        )

    def change_listen_port(self, **kwargs) -> None:
        curr_port = self._get_current_port()
        new_port = get_client_port_selection(
            self.client,
            self.settings,
            reconfigure=True,
        )

        cmd_sysctl_service("nginx", "stop")
        set_listen_port(self.client, curr_port, new_port)

        Logger.print_status(_tr("Saving new port configuration ..."))
        self.client_settings.port = new_port
        self.settings.save()
        Logger.print_ok(_tr("Port configuration saved!"))

        cmd_sysctl_service("nginx", "start")

        message = Message(
            title=_tr("Port reconfiguration complete!"),
            text=[
                _tr("Open {} now on: http://{}:{}").format(
                    self.client.display_name, get_ipv4_addr(), new_port
                ),
            ],
            color=Color.GREEN,
        )
        self.message_service.set_message(message)

    def _get_current_port(self) -> int:
        curr_port: int | None = get_nginx_listen_port(self.client.nginx_config)
        if curr_port is None:
            return int(self.client_settings.port)
        return curr_port
