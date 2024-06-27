# ======================================================================= #
#  Copyright (C) 2020 - 2024 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #

import textwrap
from typing import List

from components.webui_client.base_data import BaseWebClient
from core.menus.base_menu import print_back_footer
from utils.constants import COLOR_CYAN, COLOR_YELLOW, RESET_FORMAT
from utils.logger import DialogType, Logger


def print_moonraker_not_found_dialog():
    line1 = f"{COLOR_YELLOW}WARNING:{RESET_FORMAT}"
    line2 = f"{COLOR_YELLOW}No local Moonraker installation was found!{RESET_FORMAT}"
    dialog = textwrap.dedent(
        f"""
        /=======================================================\\
        | {line1:<63}|
        | {line2:<63}|
        |-------------------------------------------------------|
        | It is possible to install Mainsail without a local    |
        | Moonraker installation. If you continue, you need to  |
        | make sure, that Moonraker is installed on another     |
        | machine in your network. Otherwise Mainsail will NOT  |
        | work correctly.                                       |
        """
    )[1:]

    print(dialog, end="")
    print_back_footer()


def print_client_already_installed_dialog(name: str):
    line1 = f"{COLOR_YELLOW}WARNING:{RESET_FORMAT}"
    line2 = f"{COLOR_YELLOW}{name} seems to be already installed!{RESET_FORMAT}"
    line3 = f"If you continue, your current {name}"
    dialog = textwrap.dedent(
        f"""
        /=======================================================\\
        | {line1:<63}|
        | {line2:<63}|
        |-------------------------------------------------------|
        | {line3:<54}|
        | installation will be overwritten.                     |
        """
    )[1:]

    print(dialog, end="")
    print_back_footer()


def print_client_port_select_dialog(name: str, port: int, ports_in_use: List[int]):
    port = f"{COLOR_CYAN}{port}{RESET_FORMAT}"
    line1 = f"Please select the port, {name} should be served on."
    line2 = f"In case you need {name} to be served on a specific"
    dialog = textwrap.dedent(
        f"""
        /=======================================================\\
        | {line1:<54}|
        | If you are unsure what to select, hit Enter to apply  |
        | the suggested value of: {port:38} |
        |                                                       |
        | {line2:<54}|
        | port, you can set it now. Make sure the port is not   |
        | used by any other application on your system!         |
        """
    )[1:]

    if len(ports_in_use) > 0:
        dialog += "|-------------------------------------------------------|\n"
        dialog += "| The following ports were found to be in use already:  |\n"
        for port in ports_in_use:
            port = f"{COLOR_CYAN}● {port}{RESET_FORMAT}"
            dialog += f"|  {port:60}  |\n"

    dialog += "\\=======================================================/\n"

    print(dialog, end="")


def print_install_client_config_dialog(client: BaseWebClient) -> None:
    name = client.display_name
    url = client.client_config.repo_url.replace(".git", "")
    Logger.print_dialog(
        DialogType.INFO,
        [
            f"It is recommended to use special macros in order to have {name} fully "
            f"functional and working.",
            "\n\n",
            f"The recommended macros for {name} can be seen here:",
            url,
            "\n\n",
            "If you already use these macros skip this step. Otherwise you should "
            "consider to answer with 'Y' to download the recommended macros.",
        ],
        end="",
    )


def print_ipv6_warning_dialog() -> None:
    Logger.print_dialog(
        DialogType.WARNING,
        [
            "It looks like IPv6 is enabled on this system!",
            "This may cause issues with the installation of NGINX in the following "
            "steps! It is recommended to disable IPv6 on your system to avoid this issue.",
            "\n\n",
            "If you think this warning is a false alarm, and you are sure that "
            "IPv6 is disabled, you can continue with the installation.",
        ],
        end="",
    )
