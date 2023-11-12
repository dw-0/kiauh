#!/usr/bin/env python

# ======================================================================= #
#  Copyright (C) 2020 - 2023 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #

import textwrap
from typing import List

from kiauh.core.instance_manager.base_instance import BaseInstance
from kiauh.core.menus.base_menu import print_back_footer
from kiauh.utils.constants import COLOR_GREEN, RESET_FORMAT, COLOR_YELLOW, COLOR_CYAN


def print_instance_overview(
    instances: List[BaseInstance], show_index=False, show_select_all=False
):
    headline = f"{COLOR_GREEN}The following Klipper instances were found:{RESET_FORMAT}"
    dialog = textwrap.dedent(
        f"""
        /=======================================================\\
        |{headline:^64}|
        |-------------------------------------------------------|
        """
    )[1:]

    if show_select_all:
        select_all = f"{COLOR_YELLOW}a) Select all{RESET_FORMAT}"
        dialog += f"| {select_all:<63}|\n"
        dialog += "|                                                       |\n"

    for i, s in enumerate(instances):
        line = f"{COLOR_CYAN}{f'{i})' if show_index else '●'} {s.get_service_file_name()}{RESET_FORMAT}"
        dialog += f"| {line:<63}|\n"

    print(dialog, end="")
    print_back_footer()


def print_select_instance_count_dialog():
    line1 = f"{COLOR_YELLOW}WARNING:{RESET_FORMAT}"
    line2 = f"{COLOR_YELLOW}Setting up too many instances may crash your system.{RESET_FORMAT}"
    dialog = textwrap.dedent(
        f"""
        /=======================================================\\
        | Please select the number of Klipper instances to set  |
        | up. The number of Klipper instances will determine    |
        | the amount of printers you can run from this host.    |
        |                                                       |
        | {line1:<63}|
        | {line2:<63}|
        """
    )[1:]

    print(dialog, end="")
    print_back_footer()


def print_select_custom_name_dialog():
    line1 = f"{COLOR_YELLOW}INFO:{RESET_FORMAT}"
    line2 = f"{COLOR_YELLOW}Only alphanumeric characters are allowed!{RESET_FORMAT}"
    dialog = textwrap.dedent(
        f"""
        /=======================================================\\
        | You can now assign a custom name to each instance.    |
        | If skipped, each instance will get an index assigned  |
        | in ascending order, starting at index '1'.            |
        |                                                       |
        | {line1:<63}|
        | {line2:<63}|
        """
    )[1:]

    print(dialog, end="")
    print_back_footer()


def print_missing_usergroup_dialog(missing_groups) -> None:
    line1 = f"{COLOR_YELLOW}WARNING: Your current user is not in group:{RESET_FORMAT}"
    line2 = f"{COLOR_CYAN}● tty{RESET_FORMAT}"
    line3 = f"{COLOR_CYAN}● dialout{RESET_FORMAT}"
    line4 = f"{COLOR_YELLOW}INFO:{RESET_FORMAT}"
    line5 = f"{COLOR_YELLOW}Relog required for group assignments to take effect!{RESET_FORMAT}"

    dialog = textwrap.dedent(
        f"""
        /=======================================================\\
        | {line1:<63}|
        """
    )[1:]

    if "tty" in missing_groups:
        dialog += f"| {line2:<63}|\n"
    if "dialout" in missing_groups:
        dialog += f"| {line3:<63}|\n"

    dialog += textwrap.dedent(
        f"""
        |                                                       |
        | It is possible that you won't be able to successfully |
        | connect and/or flash the controller board without     |
        | your user being a member of that group.               |
        | If you want to add the current user to the group(s)   |
        | listed above, answer with 'Y'. Else skip with 'n'.    |
        |                                                       |
        | {line4:<63}|
        | {line5:<63}|
        \\=======================================================/
        """
    )[1:]

    print(dialog, end="")


def print_update_warn_dialog() -> None:
    line1 = f"{COLOR_YELLOW}WARNING:{RESET_FORMAT}"
    line2 = f"{COLOR_YELLOW}Do NOT continue if there are ongoing prints running!{RESET_FORMAT}"
    line3 = f"{COLOR_YELLOW}All Klipper instances will be restarted during the {RESET_FORMAT}"
    line4 = f"{COLOR_YELLOW}update process and ongoing prints WILL FAIL.{RESET_FORMAT}"
    dialog = textwrap.dedent(
        f"""
        /=======================================================\\
        | {line1:<63}|
        | {line2:<63}|
        | {line3:<63}|
        | {line4:<63}|
        \\=======================================================/
        """
    )[1:]

    print(dialog, end="")
