# ======================================================================= #
#  Copyright (C) 2020 - 2024 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #

import textwrap
from typing import Callable, Dict

from components.webui_client import client_remove, ClientData
from core.menus.base_menu import BaseMenu
from utils.constants import RESET_FORMAT, COLOR_RED, COLOR_CYAN


# noinspection PyUnusedLocal
class ClientRemoveMenu(BaseMenu):
    def __init__(self, client: ClientData):
        super().__init__()
        self.header = False
        self.options = self.get_options(client)

        self.client = client
        self.rm_client = False
        self.rm_client_config = False
        self.backup_mainsail_config_json = False

    def get_options(self, client: ClientData) -> Dict[str, Callable]:
        options = {
            "0": self.toggle_all,
            "1": self.toggle_rm_client,
            "2": self.toggle_rm_client_config,
            "c": self.run_removal_process,
        }
        if client.get("name") == "mainsail":
            options["3"] = self.toggle_backup_mainsail_config_json

        return options

    def print_menu(self) -> None:
        client_name = self.client.get("display_name")
        client_config = self.client.get("client_config")
        client_config_name = client_config.get("display_name")

        header = f" [ Remove {client_name} ] "
        color = COLOR_RED
        count = 62 - len(color) - len(RESET_FORMAT)
        checked = f"[{COLOR_CYAN}x{RESET_FORMAT}]"
        unchecked = "[ ]"
        o1 = checked if self.rm_client else unchecked
        o2 = checked if self.rm_client_config else unchecked
        menu = textwrap.dedent(
            f"""
            /=======================================================\\
            | {color}{header:~^{count}}{RESET_FORMAT} |
            |-------------------------------------------------------|
            | Enter a number and hit enter to select / deselect     |
            | the specific option for removal.                      |
            |-------------------------------------------------------|
            |  0) Select everything                                 |
            |-------------------------------------------------------|
            |  1) {o1} Remove {client_name:16}                       |
            |  2) {o2} Remove {client_config_name:24}               |
            """
        )[1:]

        if self.client.get("name") == "mainsail":
            o3 = checked if self.backup_mainsail_config_json else unchecked
            menu += textwrap.dedent(
                f"""
                |  3) {o3} Backup config.json                            |
                """
            )[1:]

        menu += textwrap.dedent(
            """
            |-------------------------------------------------------|
            |  C) Continue                                          |
            """
        )[1:]
        print(menu, end="")

    def toggle_all(self, **kwargs) -> None:
        self.rm_client = True
        self.rm_client_config = True
        self.backup_mainsail_config_json = True

    def toggle_rm_client(self, **kwargs) -> None:
        self.rm_client = not self.rm_client

    def toggle_rm_client_config(self, **kwargs) -> None:
        self.rm_client_config = not self.rm_client_config

    def toggle_backup_mainsail_config_json(self, **kwargs) -> None:
        self.backup_mainsail_config_json = not self.backup_mainsail_config_json

    def run_removal_process(self, **kwargs) -> None:
        if (
            not self.rm_client
            and not self.rm_client_config
            and not self.backup_mainsail_config_json
        ):
            error = f"{COLOR_RED}Nothing selected ...{RESET_FORMAT}"
            print(error)
            return

        client_remove.run_client_removal(
            client=self.client,
            rm_client=self.rm_client,
            rm_client_config=self.rm_client_config,
            backup_ms_config_json=self.backup_mainsail_config_json,
        )

        self.rm_client = False
        self.rm_client_config = False
        self.backup_mainsail_config_json = False
