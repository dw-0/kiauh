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

from components.klipper.klipper import Klipper
from components.moonraker.moonraker import Moonraker
from core.constants import COLOR_CYAN, COLOR_GREEN, COLOR_YELLOW, RESET_FORMAT
from core.menus.base_menu import print_back_footer


def print_moonraker_overview(
    klipper_instances: List[Klipper],
    moonraker_instances: List[Moonraker],
    show_index=False,
    show_select_all=False,
):
    headline = f"{COLOR_GREEN}The following instances were found:{RESET_FORMAT}"
    dialog = textwrap.dedent(
        f"""
        ╔═══════════════════════════════════════════════════════╗
        ║{headline:^64}║
        ╟───────────────────────────────────────────────────────╢
        """
    )[1:]

    if show_select_all:
        select_all = f"{COLOR_YELLOW}a) Select all{RESET_FORMAT}"
        dialog += f"║ {select_all:<63}║\n"
        dialog += "║                                                       ║\n"

    instance_map = {
        k.service_file_path.stem: (
            k.service_file_path.stem.replace("klipper", "moonraker")
            if k.suffix in [m.suffix for m in moonraker_instances]
            else ""
        )
        for k in klipper_instances
    }

    for i, k in enumerate(instance_map):
        mr_name = instance_map.get(k)
        m = f"<-> {mr_name}" if mr_name != "" else ""
        line = f"{COLOR_CYAN}{f'{i+1})' if show_index else '●'} {k} {m} {RESET_FORMAT}"
        dialog += f"║ {line:<63}║\n"

    warn_l1 = f"{COLOR_YELLOW}PLEASE NOTE: {RESET_FORMAT}"
    warn_l2 = f"{COLOR_YELLOW}If you select an instance with an existing Moonraker{RESET_FORMAT}"
    warn_l3 = f"{COLOR_YELLOW}instance, that Moonraker instance will be re-created!{RESET_FORMAT}"
    warning = textwrap.dedent(
        f"""
        ║                                                       ║
        ╟───────────────────────────────────────────────────────╢
        ║ {warn_l1:<63}║
        ║ {warn_l2:<63}║
        ║ {warn_l3:<63}║
        ╟───────────────────────────────────────────────────────╢
        """
    )[1:]

    dialog += warning

    print(dialog, end="")
    print_back_footer()
