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
        | It is possible to install Mainsail without a local    |
        | Moonraker installation. If you continue, you need to  |
        | make sure, that Moonraker is installed on another     |
        | machine in your network. Otherwise Mainsail will NOT  |
        | work correctly.                                       |
        """
    )[1:]

    print(dialog, end="")
    print_back_footer()


def print_mainsail_already_installed_dialog():
    line1 = f"{COLOR_YELLOW}WARNING:{RESET_FORMAT}"
    line2 = f"{COLOR_YELLOW}Mainsail seems to be already installed!{RESET_FORMAT}"
    dialog = textwrap.dedent(
        f"""
        /=======================================================\\
        | {line1:<63}|
        | {line2:<63}|
        |-------------------------------------------------------|
        | If you continue, your current Mainsail installation   |
        | will be overwritten. You will not loose any printer   |
        | configurations and the Moonraker database will remain |
        | untouched.                                            |
        """
    )[1:]

    print(dialog, end="")
    print_back_footer()


def print_install_mainsail_config_dialog():
    dialog = textwrap.dedent(
        f"""
        /=======================================================\\
        | It is recommended to use special macros in order to   |
        | have Mainsail fully functional and working.           |
        |                                                       |
        | The recommended macros for Mainsail can be seen here: |
        | https://github.com/mainsail-crew/mainsail-config      |
        |                                                       |
        | If you already use these macros skip this step.       |
        | Otherwise you should consider to answer with 'Y' to   |
        | download the recommended macros.                      |
        \\=======================================================/
        """
    )[1:]

    print(dialog, end="")


def print_mainsail_port_select_dialog(port: str):
    port = f"{COLOR_CYAN}{port}{RESET_FORMAT}"
    dialog = textwrap.dedent(
        f"""
        /=======================================================\\
        | Please select the port, Mainsail should be served on. |
        | If you are unsure what to select, hit Enter to apply  |
        | the suggested value of: {port:38} |
        |                                                       |
        | In case you need Mainsail to be served on a specific  |
        | port, you can set it now. Make sure the port is not   |
        | used by any other application on your system!         |
        \\=======================================================/
        """
    )[1:]

    print(dialog, end="")
