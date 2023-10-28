#!/usr/bin/env python

# ======================================================================= #
#  Copyright (C) 2020 - 2023 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #

from typing import List

from kiauh.instance_manager.base_instance import BaseInstance
from kiauh.menus.base_menu import print_back_footer
from kiauh.utils.constants import COLOR_GREEN, COLOR_CYAN, COLOR_YELLOW, RESET_FORMAT


def print_instance_overview(
    instances: List[BaseInstance], show_index=False, show_select_all=False
):
    headline = f"{COLOR_GREEN}The following Klipper instances were found:{RESET_FORMAT}"

    print("/=======================================================\\")
    print(f"|{'{:^64}'.format(headline)}|")
    print("|-------------------------------------------------------|")

    if show_select_all:
        select_all = f"  {COLOR_YELLOW}a) Select all{RESET_FORMAT}"
        print(f"|{'{:64}'.format(select_all)}|")
        print("|                                                       |")

    for i, s in enumerate(instances):
        index = f"{i})" if show_index else "●"
        instance = s.get_service_file_name()
        line = f"{'{:53}'.format(f'{index} {instance}')}"
        print(f"|  {COLOR_CYAN}{line}{RESET_FORMAT}|")

    print_back_footer()


def print_missing_usergroup_dialog(missing_groups) -> None:
    print("/=======================================================\\")
    print(
        f"| {COLOR_YELLOW}WARNING: Your current user is not in group:{RESET_FORMAT}           |"
    )
    if "tty" in missing_groups:
        print(
            f"| {COLOR_CYAN}● tty{RESET_FORMAT}                                                 |"
        )
    if "dialout" in missing_groups:
        print(
            f"| {COLOR_CYAN}● dialout{RESET_FORMAT}                                             |"
        )
    print("|                                                       |")
    print("| It is possible that you won't be able to successfully |")
    print("| connect and/or flash the controller board without     |")
    print("| your user being a member of that group.               |")
    print("| If you want to add the current user to the group(s)   |")
    print("| listed above, answer with 'Y'. Else skip with 'n'.    |")
    print("|                                                       |")
    print(
        f"| {COLOR_YELLOW}INFO:{RESET_FORMAT}                                                 |"
    )
    print(
        f"| {COLOR_YELLOW}Relog required for group assignments to take effect!{RESET_FORMAT}  |"
    )
    print("\\=======================================================/")
