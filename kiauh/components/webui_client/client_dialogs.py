# ======================================================================= #
#  Copyright (C) 2020 - 2024 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #

from typing import List

from components.webui_client.base_data import BaseWebClient
from core.logger import DialogType, Logger


def print_moonraker_not_found_dialog() -> None:
    Logger.print_dialog(
        DialogType.WARNING,
        [
            "No local Moonraker installation was found!",
            "\n\n",
            "It is possible to install Mainsail without a local Moonraker installation. "
            "If you continue, you need to make sure, that Moonraker is installed on "
            "another machine in your network. Otherwise Mainsail will NOT work "
            "correctly.",
        ],
    )


def print_client_already_installed_dialog(name: str) -> None:
    Logger.print_dialog(
        DialogType.WARNING,
        [
            f"{name} seems to be already installed!",
            f"If you continue, your current {name} installation will be overwritten.",
        ],
    )


def print_client_port_select_dialog(
    name: str, port: int, ports_in_use: List[int]
) -> None:
    Logger.print_dialog(
        DialogType.CUSTOM,
        [
            f"Please select the port, {name} should be served on. If your are unsure "
            f"what to select, hit Enter to apply the suggested value of: {port}",
            "\n\n",
            f"In case you need {name} to be served on a specific port, you can set it "
            f"now. Make sure that the port is not already used by another application "
            f"on your system!",
            "\n\n",
            "The following ports were found to be in use already:",
            *[f"● {port}" for port in ports_in_use],
        ],
    )


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
    )
