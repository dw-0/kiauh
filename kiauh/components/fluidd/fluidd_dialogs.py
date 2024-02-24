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
from typing import List

from core.menus.base_menu import print_back_footer
from utils.constants import RESET_FORMAT, COLOR_YELLOW, COLOR_CYAN


def print_moonraker_not_found_dialog():
    line1 = f"{COLOR_YELLOW}WARNING:{RESET_FORMAT}"
    line2 = f"{COLOR_YELLOW}No local Moonraker installation was found!{RESET_FORMAT}"
    dialog = textwrap.dedent(
        f"""
        /=======================================================\\
        | {line1:<63}|
        | {line2:<63}|
        |-------------------------------------------------------|
        | It is possible to install Fluidd without a local      |
        | Moonraker installation. If you continue, you need to  |
        | make sure, that Moonraker is installed on another     |
        | machine in your network. Otherwise Fluidd will NOT    |
        | work correctly.                                       |
        """
    )[1:]

    print(dialog, end="")
    print_back_footer()


def print_fluidd_already_installed_dialog():
    line1 = f"{COLOR_YELLOW}WARNING:{RESET_FORMAT}"
    line2 = f"{COLOR_YELLOW}Fluidd seems to be already installed!{RESET_FORMAT}"
    dialog = textwrap.dedent(
        f"""
        /=======================================================\\
        | {line1:<63}|
        | {line2:<63}|
        |-------------------------------------------------------|
        | If you continue, your current Fluidd installation     |
        | will be overwritten. You will not loose any printer   |
        | configurations and the Moonraker database will remain |
        | untouched.                                            |
        """
    )[1:]

    print(dialog, end="")
    print_back_footer()


def print_install_fluidd_config_dialog():
    dialog = textwrap.dedent(
        f"""
        /=======================================================\\
        | It is recommended to use special macros in order to   |
        | have Fluidd fully functional and working.             |
        |                                                       |
        | The recommended macros for Fluidd can be seen here:   |
        | https://github.com/fluidd-core/fluidd-config          |
        |                                                       |
        | If you already use these macros skip this step.       |
        | Otherwise you should consider to answer with 'Y' to   |
        | download the recommended macros.                      |
        \\=======================================================/
        """
    )[1:]

    print(dialog, end="")


def print_fluidd_port_select_dialog(port: str, ports_in_use: List[str]):
    port = f"{COLOR_CYAN}{port}{RESET_FORMAT}"
    dialog = textwrap.dedent(
        f"""
        /=======================================================\\
        | Please select the port, Fluidd should be served on.   |
        | If you are unsure what to select, hit Enter to apply  |
        | the suggested value of: {port:38} |
        |                                                       |
        | In case you need Fluidd to be served on a specific    |
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
