# ======================================================================= #
#  Copyright (C) 2020 - 2025 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #

from typing import List

from components.webui_client.base_data import BaseWebClient
from core.logger import DialogType, Logger


def print_moonraker_not_found_dialog(name: str) -> None:
    Logger.print_dialog(
        DialogType.WARNING,
        [
            "No local Moonraker installation was found!",
            "\n\n",
            f"It is possible to install {name} without a local Moonraker installation. "
            "If you continue, you need to make sure, that Moonraker is installed on "
            f"another machine in your network. Otherwise {name} will NOT work "
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
    dialog_content: List[str] = [
        f"Please select the port, {name} should be served on. If your are unsure "
        f"what to select, hit Enter to apply the suggested value of: {port}",
        "\n\n",
        f"In case you need {name} to be served on a specific port, you can set it "
        f"now. Make sure that the port is not already used by another application "
        f"on your system!",
    ]

    if ports_in_use:
        dialog_content.extend(
            [
                "\n\n",
                "The following ports were found to be already in use:",
                *[f"● {p}" for p in ports_in_use if p != port],
            ]
        )

    Logger.print_dialog(DialogType.CUSTOM, dialog_content)


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
