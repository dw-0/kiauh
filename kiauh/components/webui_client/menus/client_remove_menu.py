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
from typing import Callable, Dict

from components.webui_client import client_remove, ClientData
from core.menus import BACK_HELP_FOOTER
from core.menus.base_menu import BaseMenu
from utils.constants import RESET_FORMAT, COLOR_RED, COLOR_CYAN


# noinspection PyUnusedLocal
class ClientRemoveMenu(BaseMenu):
    def __init__(self, client: ClientData):
        self.client = client
        self.rm_client = False
        self.rm_client_config = False
        self.backup_mainsail_config_json = False
        self.rm_moonraker_conf_section = False
        self.rm_printer_cfg_section = False

        super().__init__(
            header=False,
            options=self.get_options(),
            footer_type=BACK_HELP_FOOTER,
        )

    def get_options(self) -> Dict[str, Callable]:
        options = {
            "0": self.toggle_all,
            "1": self.toggle_rm_client,
            "2": self.toggle_rm_client_config,
            "3": self.toggle_rm_printer_cfg_section,
            "4": self.toggle_rm_moonraker_conf_section,
            "c": self.run_removal_process,
        }
        if self.client.get("name") == "mainsail":
            options["5"] = self.toggle_backup_mainsail_config_json

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
        o3 = checked if self.rm_printer_cfg_section else unchecked
        o4 = checked if self.rm_moonraker_conf_section else unchecked
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
            |                                                       |
            | printer.cfg & moonraker.conf                          |
            |  3) {o3} Remove printer.cfg include                    |
            |  4) {o4} Remove Moonraker update section               |
            """
        )[1:]

        if self.client.get("name") == "mainsail":
            o5 = checked if self.backup_mainsail_config_json else unchecked
            menu += textwrap.dedent(
                f"""
                |                                                       |
                | Mainsail config.json                                  |
                |  5) {o5} Backup config.json                            |
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
        self.rm_moonraker_conf_section = True
        self.rm_printer_cfg_section = True

    def toggle_rm_client(self, **kwargs) -> None:
        self.rm_client = not self.rm_client

    def toggle_rm_client_config(self, **kwargs) -> None:
        self.rm_client_config = not self.rm_client_config

    def toggle_backup_mainsail_config_json(self, **kwargs) -> None:
        self.backup_mainsail_config_json = not self.backup_mainsail_config_json

    def toggle_rm_moonraker_conf_section(self, **kwargs) -> None:
        self.rm_moonraker_conf_section = not self.rm_moonraker_conf_section

    def toggle_rm_printer_cfg_section(self, **kwargs) -> None:
        self.rm_printer_cfg_section = not self.rm_printer_cfg_section

    def run_removal_process(self, **kwargs) -> None:
        if (
            not self.rm_client
            and not self.rm_client_config
            and not self.backup_mainsail_config_json
            and not self.rm_moonraker_conf_section
            and not self.rm_printer_cfg_section
        ):
            error = f"{COLOR_RED}Nothing selected ...{RESET_FORMAT}"
            print(error)
            return

        client_remove.run_client_removal(
            client=self.client,
            rm_client=self.rm_client,
            rm_client_config=self.rm_client_config,
            backup_ms_config_json=self.backup_mainsail_config_json,
            rm_moonraker_conf_section=self.rm_moonraker_conf_section,
            rm_printer_cfg_section=self.rm_printer_cfg_section,
        )

        self.rm_client = False
        self.rm_client_config = False
        self.backup_mainsail_config_json = False
        self.rm_moonraker_conf_section = False
        self.rm_printer_cfg_section = False
