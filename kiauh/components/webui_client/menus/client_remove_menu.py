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

from components.webui_client import client_remove
from components.webui_client.base_data import BaseWebClient
from core.constants import COLOR_CYAN, COLOR_RED, RESET_FORMAT
from core.menus import Option
from core.menus.base_menu import BaseMenu


# noinspection PyUnusedLocal
class ClientRemoveMenu(BaseMenu):
    def __init__(
        self, client: BaseWebClient, previous_menu: Type[BaseMenu] | None = None
    ):
        super().__init__()
        self.previous_menu: Type[BaseMenu] | None = previous_menu
        self.client: BaseWebClient = client
        self.remove_client: bool = False
        self.remove_client_cfg: bool = False
        self.backup_config_json: bool = False
        self.selection_state: bool = False

    def set_previous_menu(self, previous_menu: Type[BaseMenu] | None) -> None:
        from core.menus.remove_menu import RemoveMenu

        self.previous_menu = previous_menu if previous_menu is not None else RemoveMenu

    def set_options(self) -> None:
        self.options = {
            "a": Option(method=self.toggle_all),
            "1": Option(method=self.toggle_rm_client),
            "2": Option(method=self.toggle_rm_client_config),
            "3": Option(method=self.toggle_backup_config_json),
            "c": Option(method=self.run_removal_process),
        }

    def print_menu(self) -> None:
        client_name = self.client.display_name
        client_config = self.client.client_config
        client_config_name = client_config.display_name

        header = f" [ Remove {client_name} ] "
        color = COLOR_RED
        count = 62 - len(color) - len(RESET_FORMAT)
        checked = f"[{COLOR_CYAN}x{RESET_FORMAT}]"
        unchecked = "[ ]"
        o1 = checked if self.remove_client else unchecked
        o2 = checked if self.remove_client_cfg else unchecked
        o3 = checked if self.backup_config_json else unchecked
        menu = textwrap.dedent(
            f"""
            ╔═══════════════════════════════════════════════════════╗
            ║ {color}{header:~^{count}}{RESET_FORMAT} ║
            ╟───────────────────────────────────────────────────────╢
            ║ Enter a number and hit enter to select / deselect     ║
            ║ the specific option for removal.                      ║
            ╟───────────────────────────────────────────────────────╢
            ║  a) {self._get_selection_state_str():37}             ║
            ╟───────────────────────────────────────────────────────╢
            ║  1) {o1} Remove {client_name:16}                       ║
            ║  2) {o2} Remove {client_config_name:24}               ║
            ║  3) {o3} Backup config.json                            ║
            ╟───────────────────────────────────────────────────────╢
            ║  C) Continue                                          ║
            ╟───────────────────────────────────────────────────────╢
            """
        )[1:]
        print(menu, end="")

    def toggle_all(self, **kwargs) -> None:
        self.selection_state = not self.selection_state
        self.remove_client = self.selection_state
        self.remove_client_cfg = self.selection_state
        self.backup_config_json = self.selection_state

    def toggle_rm_client(self, **kwargs) -> None:
        self.remove_client = not self.remove_client

    def toggle_rm_client_config(self, **kwargs) -> None:
        self.remove_client_cfg = not self.remove_client_cfg

    def toggle_backup_config_json(self, **kwargs) -> None:
        self.backup_config_json = not self.backup_config_json

    def run_removal_process(self, **kwargs) -> None:
        if (
            not self.remove_client
            and not self.remove_client_cfg
            and not self.backup_config_json
        ):
            error = f"{COLOR_RED}Nothing selected ...{RESET_FORMAT}"
            print(error)
            return

        client_remove.run_client_removal(
            client=self.client,
            remove_client=self.remove_client,
            remove_client_cfg=self.remove_client_cfg,
            backup_config=self.backup_config_json,
        )

        self.remove_client = False
        self.remove_client_cfg = False
        self.backup_config_json = False

        self._go_back()

    def _get_selection_state_str(self) -> str:
        return (
            "Select everything" if not self.selection_state else "Deselect everything"
        )

    def _go_back(self, **kwargs) -> None:
        if self.previous_menu is not None:
            self.previous_menu().run()
