# ======================================================================= #
#  Copyright (C) 2020 - 2025 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #

import textwrap
from enum import Enum, unique
from typing import List

from core.menus.base_menu import print_back_footer
from core.types.color import Color
from utils.instance_type import InstanceType


@unique
class DisplayType(Enum):
    SERVICE_NAME = "SERVICE_NAME"
    PRINTER_NAME = "PRINTER_NAME"


def print_instance_overview(
    instances: List[InstanceType],
    display_type: DisplayType = DisplayType.SERVICE_NAME,
    show_headline=True,
    show_index=False,
    start_index=0,
    show_select_all=False,
) -> None:
    dialog = "╔═══════════════════════════════════════════════════════╗\n"
    if show_headline:
        d_type = (
            "Klipper instances"
            if display_type is DisplayType.SERVICE_NAME
            else "printer directories"
        )
        headline = Color.apply(f"The following {d_type} were found:", Color.GREEN)
        dialog += f"║{headline:^64}║\n"
        dialog += "╟───────────────────────────────────────────────────────╢\n"

    if show_select_all:
        select_all = Color.apply("a) Select all", Color.YELLOW)
        dialog += f"║ {select_all:<63}║\n"
        dialog += "║                                                       ║\n"

    for i, s in enumerate(instances):
        if display_type is DisplayType.SERVICE_NAME:
            name = s.service_file_path.stem
        else:
            name = s.data_dir
        line = Color.apply(
            f"{f'{i + start_index})' if show_index else '●'} {name}", Color.CYAN
        )
        dialog += f"║ {line:<63}║\n"
    dialog += "╟───────────────────────────────────────────────────────╢\n"

    print(dialog, end="")
    print_back_footer()


def print_select_instance_count_dialog() -> None:
    line1 = Color.apply("WARNING:", Color.YELLOW)
    line2 = Color.apply(
        "Setting up too many instances may crash your system.", Color.YELLOW
    )
    dialog = textwrap.dedent(
        f"""
        ╔═══════════════════════════════════════════════════════╗
        ║ Please select the number of Klipper instances to set  ║
        ║ up. The number of Klipper instances will determine    ║
        ║ the amount of printers you can run from this host.    ║
        ║                                                       ║
        ║ {line1:<63}║
        ║ {line2:<63}║
        ╟───────────────────────────────────────────────────────╢
        """
    )[1:]

    print(dialog, end="")
    print_back_footer()


def print_select_custom_name_dialog() -> None:
    line1 = Color.apply("INFO:", Color.YELLOW)
    line2 = Color.apply("Only alphanumeric characters are allowed!", Color.YELLOW)
    dialog = textwrap.dedent(
        f"""
        ╔═══════════════════════════════════════════════════════╗
        ║ Do you want to assign a custom name to each instance? ║
        ║                                                       ║
        ║ Assigning a custom name will create a Klipper service ║
        ║ and a printer directory with the chosen name.         ║
        ║                                                       ║
        ║ Example for custom name 'kiauh':                      ║
        ║  ● Klipper service:   klipper-kiauh.service           ║
        ║  ● Printer directory: printer_kiauh_data              ║
        ║                                                       ║
        ║ If skipped, each instance will get an index assigned  ║
        ║ in ascending order, starting at '1' in case of a new  ║
        ║ installation. Otherwise, the index will be derived    ║
        ║ from amount of already existing instances.            ║
        ║                                                       ║
        ║ {line1:<63}║
        ║ {line2:<63}║
        ╟───────────────────────────────────────────────────────╢
        """
    )[1:]

    print(dialog, end="")
    print_back_footer()
