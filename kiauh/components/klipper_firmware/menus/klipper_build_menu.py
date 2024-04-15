# ======================================================================= #
#  Copyright (C) 2020 - 2024 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #

import textwrap
from typing import Type, Optional

from components.klipper import KLIPPER_DIR
from components.klipper_firmware.firmware_utils import (
    run_make_clean,
    run_make_menuconfig,
    run_make,
)
from core.menus import Option
from core.menus.base_menu import BaseMenu
from utils.constants import COLOR_CYAN, RESET_FORMAT, COLOR_GREEN, COLOR_RED
from utils.logger import Logger
from utils.system_utils import (
    check_package_install,
    update_system_package_lists,
    install_system_packages,
)


# noinspection PyUnusedLocal
# noinspection PyMethodMayBeStatic
class KlipperBuildFirmwareMenu(BaseMenu):
    def __init__(self, previous_menu: Optional[Type[BaseMenu]] = None):
        super().__init__()
        self.previous_menu = previous_menu
        self.deps = ["build-essential", "dpkg-dev", "make"]
        self.missing_deps = check_package_install(self.deps)

    def set_previous_menu(self, previous_menu: Optional[Type[BaseMenu]]) -> None:
        from core.menus.advanced_menu import AdvancedMenu

        self.previous_menu: Type[BaseMenu] = (
            previous_menu if previous_menu is not None else AdvancedMenu
        )

    def set_options(self) -> None:
        if len(self.missing_deps) == 0:
            self.input_label_txt = "Press ENTER to continue"
            self.default_option = Option(method=self.start_build_process, menu=False)
        else:
            self.input_label_txt = "Press ENTER to install dependencies"
            self.default_option = Option(method=self.install_missing_deps, menu=False)

    def print_menu(self) -> None:
        header = " [ Build Firmware Menu ] "
        color = COLOR_CYAN
        count = 62 - len(color) - len(RESET_FORMAT)
        menu = textwrap.dedent(
            f"""
            /=======================================================\\
            | {color}{header:~^{count}}{RESET_FORMAT} |
            |-------------------------------------------------------|
            | The following dependencies are required:              |
            |                                                       |
            """
        )[1:]

        for d in self.deps:
            status_ok = f"{COLOR_GREEN}*INSTALLED*{RESET_FORMAT}"
            status_missing = f"{COLOR_RED}*MISSING*{RESET_FORMAT}"
            status = status_missing if d in self.missing_deps else status_ok
            padding = 39 - len(d) + len(status) + (len(status_ok) - len(status))
            d = f" {COLOR_CYAN}● {d}{RESET_FORMAT}"
            menu += f"| {d}{status:>{padding}} |\n"

        menu += "|                                                       |\n"
        if len(self.missing_deps) == 0:
            line = f"{COLOR_GREEN}All dependencies are met!{RESET_FORMAT}"
        else:
            line = f"{COLOR_RED}Dependencies are missing!{RESET_FORMAT}"

        menu += f"| {line:<62} |\n"

        print(menu, end="")

    def install_missing_deps(self, **kwargs) -> None:
        try:
            update_system_package_lists(silent=False)
            Logger.print_status("Installing system packages...")
            install_system_packages(self.missing_deps)
        except Exception as e:
            Logger.print_error(e)
            Logger.print_error("Installding dependencies failed!")
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
            self.previous_menu().run()
