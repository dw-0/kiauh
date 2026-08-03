# ======================================================================= #
#  Copyright (C) 2020 - 2026 Dominik Willner <dev.dw-0@proton.me>         #
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
from core.i18n import _tr
from core.menus.base_menu import print_back_footer
from core.types.color import Color


def print_moonraker_overview(
    klipper_instances: List[Klipper],
    moonraker_instances: List[Moonraker],
    show_index=False,
    show_select_all=False,
):
    headline = Color.apply(_tr("The following instances were found:"), Color.GREEN)
    dialog = textwrap.dedent(
        f"""
        ╔═══════════════════════════════════════════════════════╗
        ║{headline:^64}║
        ╟───────────────────────────────────────────────────────╢
        """
    )[1:]

    if show_select_all:
        select_all = Color.apply(_tr("a) Select all"), Color.YELLOW)
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
        line = Color.apply(
            _tr("{} {} {}").format(
                f"{i + 1})" if show_index else "●",
                k,
                m,
            ),
            Color.CYAN,
        )
        dialog += f"║ {line:<63}║\n"

    warn_l1 = Color.apply(_tr("PLEASE NOTE:"), Color.YELLOW)
    warn_l2 = Color.apply(
        _tr("If you select an instance with an existing Moonraker"), Color.YELLOW
    )
    warn_l3 = Color.apply(
        _tr("instance, that Moonraker instance will be re-created!"), Color.YELLOW
    )
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
