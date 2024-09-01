# ======================================================================= #
#  Copyright (C) 2020 - 2024 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #
from __future__ import annotations

import textwrap
from typing import List, Set, Type

from components.klipper import KLIPPER_DIR
from components.klipper_firmware.firmware_utils import (
    run_make,
    run_make_clean,
    run_make_menuconfig,
)
from core.constants import COLOR_CYAN, COLOR_GREEN, COLOR_RED, RESET_FORMAT
from core.logger import Logger
from core.menus import Option
from core.menus.base_menu import BaseMenu
from utils.sys_utils import (
    check_package_install,
    install_system_packages,
    update_system_package_lists,
)


# noinspection PyUnusedLocal
# noinspection PyMethodMayBeStatic
class KlipperBuildFirmwareMenu(BaseMenu):
    def __init__(self, previous_menu: Type[BaseMenu] | None = None):
        super().__init__()
        self.previous_menu: Type[BaseMenu] | None = previous_menu
        self.deps: Set[str] = {"build-essential", "dpkg-dev", "make"}
        self.missing_deps: List[str] = check_package_install(self.deps)

    def set_previous_menu(self, previous_menu: Type[BaseMenu] | None) -> None:
        from core.menus.advanced_menu import AdvancedMenu

        self.previous_menu = (
            previous_menu if previous_menu is not None else AdvancedMenu
        )

    def set_options(self) -> None:
        if len(self.missing_deps) == 0:
            self.input_label_txt = "Press ENTER to continue"
            self.default_option = Option(method=self.start_build_process)
        else:
            self.input_label_txt = "Press ENTER to install dependencies"
            self.default_option = Option(method=self.install_missing_deps)

    def print_menu(self) -> None:
        header = " [ Build Firmware Menu ] "
        color = COLOR_CYAN
        count = 62 - len(color) - len(RESET_FORMAT)
        menu = textwrap.dedent(
            f"""
            ╔═══════════════════════════════════════════════════════╗
            ║ {color}{header:~^{count}}{RESET_FORMAT} ║
            ╟───────────────────────────────────────────────────────╢
            ║ The following dependencies are required:              ║
            ║                                                       ║
            """
        )[1:]

        for d in self.deps:
            status_ok = f"{COLOR_GREEN}*INSTALLED*{RESET_FORMAT}"
            status_missing = f"{COLOR_RED}*MISSING*{RESET_FORMAT}"
            status = status_missing if d in self.missing_deps else status_ok
            padding = 39 - len(d) + len(status) + (len(status_ok) - len(status))
            d = f" {COLOR_CYAN}● {d}{RESET_FORMAT}"
            menu += f"║ {d}{status:>{padding}} ║\n"
        menu += "║                                                       ║\n"

        if len(self.missing_deps) == 0:
            line = f"{COLOR_GREEN}All dependencies are met!{RESET_FORMAT}"
        else:
            line = f"{COLOR_RED}Dependencies are missing!{RESET_FORMAT}"

        menu += f"║ {line:<62} ║\n"
        menu += "╟───────────────────────────────────────────────────────╢\n"

        print(menu, end="")

    def install_missing_deps(self, **kwargs) -> None:
        try:
            update_system_package_lists(silent=False)
            Logger.print_status("Installing system packages...")
            install_system_packages(self.missing_deps)
        except Exception as e:
            Logger.print_error(e)
            Logger.print_error("Installing dependencies failed!")
        finally:
            # restart this menu
            KlipperBuildFirmwareMenu().run()

    def start_build_process(self, **kwargs) -> None:
        try:
            run_make_clean()
            run_make_menuconfig()
            run_make()

            Logger.print_ok("Firmware successfully built!")
            Logger.print_ok(f"Firmware file located in '{KLIPPER_DIR}/out'!")

        except Exception as e:
            Logger.print_error(e)
            Logger.print_error("Building Klipper Firmware failed!")

        finally:
            if self.previous_menu is not None:
                self.previous_menu().run()
