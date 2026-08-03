# ======================================================================= #
#  Copyright (C) 2020 - 2026 Dominik Willner <dev.dw-0@proton.me>         #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #

from typing import List

from components.webui_client.base_data import BaseWebClient
from core.i18n import _tr
from core.logger import DialogType, Logger


def print_moonraker_not_found_dialog(name: str) -> None:
    Logger.print_dialog(
        DialogType.WARNING,
        [
            _tr("No local Moonraker installation was found!"),
            "\n\n",
            _tr("It is possible to install {} without a local Moonraker installation. "
                "If you continue, you need to make sure, that Moonraker is installed on "
                "another machine in your network. Otherwise {} will NOT work "
                "correctly.").format(name, name),
        ],
    )


def print_client_already_installed_dialog(name: str) -> None:
    Logger.print_dialog(
        DialogType.WARNING,
        [
            _tr("{} seems to be already installed!").format(name),
            _tr("If you continue, your current {} installation will be overwritten.").format(name),
        ],
    )


def print_client_port_select_dialog(
    name: str, port: int, ports_in_use: List[int]
) -> None:
    dialog_content: List[str] = [
        _tr("Please select the port, {} should be served on. If your are unsure "
            "what to select, hit Enter to apply the suggested value of: {}").format(name, port),
        "\n\n",
        _tr("In case you need {} to be served on a specific port, you can set it "
            "now. Make sure that the port is not already used by another application "
            "on your system!").format(name),
    ]

    if ports_in_use:
        dialog_content.extend(
            [
                "\n\n",
                _tr("The following ports were found to be already in use:"),
                *[_tr("● {}").format(p) for p in ports_in_use if p != port],
            ]
        )

    Logger.print_dialog(DialogType.CUSTOM, dialog_content)


def print_install_client_config_dialog(client: BaseWebClient) -> None:
    name = client.display_name
    url = client.client_config.repo_url.replace(".git", "")
    Logger.print_dialog(
        DialogType.INFO,
        [
            _tr("It is recommended to use special macros in order to have {} fully "
                "functional and working.").format(name),
            "\n\n",
            _tr("The recommended macros for {} can be seen here:").format(name),
            url,
            "\n\n",
            _tr("If you already use these macros skip this step. Otherwise you should "
                "consider to answer with 'Y' to download the recommended macros."),
        ],
    )


def print_ipv6_warning_dialog() -> None:
    Logger.print_dialog(
        DialogType.WARNING,
        [
            _tr("It looks like IPv6 is enabled on this system!"),
            _tr("This may cause issues with the installation of NGINX in the following "
                "steps! It is recommended to disable IPv6 on your system to avoid this issue."),
            "\n\n",
            _tr("If you think this warning is a false alarm, and you are sure that "
                "IPv6 is disabled, you can continue with the installation."),
        ],
    )
