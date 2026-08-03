# ======================================================================= #
#  Copyright (C) 2020 - 2026 Dominik Willner <dev.dw-0@proton.me>         #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #

import textwrap
from enum import Enum, unique
from typing import List

from core.i18n import _tr
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
            _tr("Klipper instances")
            if display_type is DisplayType.SERVICE_NAME
            else _tr("printer directories")
        )
        headline = Color.apply(_tr("The following {} were found:").format(d_type), Color.GREEN)
        dialog += f"║{headline:^64}║\n"
        dialog += "╟───────────────────────────────────────────────────────╢\n"

    if show_select_all:
        select_all = Color.apply(_tr("a) Select all"), Color.YELLOW)
        dialog += f"║ {select_all:<63}║\n"
        dialog += "║                                                       ║\n"

    for i, s in enumerate(instances):
        if display_type is DisplayType.SERVICE_NAME:
            name = s.service_file_path.stem
        else:
            name = s.data_dir
        line = Color.apply(
            _tr("{} {}").format(
                f"{i + start_index})" if show_index else "●",
                name,
            ),
            Color.CYAN,
        )
        dialog += f"║ {line:<63}║\n"
    dialog += "╟───────────────────────────────────────────────────────╢\n"

    print(dialog, end="")
    print_back_footer()


def print_select_instance_count_dialog() -> None:
    line1 = Color.apply(_tr("WARNING:"), Color.YELLOW)
    line2 = Color.apply(
        _tr("Setting up too many instances may crash your system."), Color.YELLOW
    )
    dialog = textwrap.dedent(
        f"""
        ╔═══════════════════════════════════════════════════════╗
        ║ {_tr("Please select the number of Klipper instances to set"):<62}║
        ║ {_tr("up. The number of Klipper instances will determine"):<62}║
        ║ {_tr("the amount of printers you can run from this host."):<62}║
        ║                                                       ║
        ║ {line1:<63}║
        ║ {line2:<63}║
        ╟───────────────────────────────────────────────────────╢
        """
    )[1:]

    print(dialog, end="")
    print_back_footer()


def print_select_custom_name_dialog() -> None:
    line1 = Color.apply(_tr("INFO:"), Color.YELLOW)
    line2 = Color.apply(_tr("Only alphanumeric characters are allowed!"), Color.YELLOW)
    dialog = textwrap.dedent(
        f"""
        ╔═══════════════════════════════════════════════════════╗
        ║ {_tr("Do you want to assign a custom name to each instance?"):<62}║
        ║                                                       ║
        ║ {_tr("Assigning a custom name will create a Klipper service"):<62}║
        ║ {_tr("and a printer directory with the chosen name."):<62}║
        ║                                                       ║
        ║ {_tr("Example for custom name 'kiauh':"):<62}║
        ║  ● Klipper service:   klipper-kiauh.service           ║
        ║  ● Printer directory: printer_kiauh_data              ║
        ║                                                       ║
        ║ {_tr("If skipped, each instance will get an index assigned"):<62}║
        ║ {_tr("in ascending order, starting at '1' in case of a new"):<62}║
        ║ {_tr("installation. Otherwise, the index will be derived"):<62}║
        ║ {_tr("from amount of already existing instances."):<62}║
        ║                                                       ║
        ║ {line1:<63}║
        ║ {line2:<63}║
        ╟───────────────────────────────────────────────────────╢
        """
    )[1:]

    print(dialog, end="")
    print_back_footer()
