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
from os import listdir, mkdir, path
from shutil import copyfile
from typing import List, Set, Type

from components.klipper import KLIPPER_DIR, KLIPPER_KCONFIGS_DIR
from components.klipper_firmware.firmware_utils import (
    run_make,
    run_make_clean,
    run_make_menuconfig,
)
from components.klipper_firmware.flash_options import FlashOptions
from core.logger import DialogType, Logger
from core.menus import Option
from core.menus.base_menu import BaseMenu
from core.types.color import Color
from utils.input_utils import get_confirm, get_string_input
from utils.sys_utils import (
    check_package_install,
    install_system_packages,
    update_system_package_lists,
)


# noinspection PyUnusedLocal
# noinspection PyMethodMayBeStatic
class KlipperKConfigMenu(BaseMenu):
    def __init__(self, previous_menu: Type[BaseMenu] | None = None):
        super().__init__()
        self.title = "Firmware Config Menu"
        self.title_color = Color.CYAN
        self.previous_menu: Type[BaseMenu] | None = previous_menu
        self.flash_options = FlashOptions()
        self.kconfigs_dirname = KLIPPER_KCONFIGS_DIR
        self.kconfig_default = path.join(KLIPPER_DIR, ".config")
        self.kconfig = (
            self.kconfig_default if not path.isdir(self.kconfigs_dirname) else None
        )

    def run(self) -> None:
        if not self.kconfig:
            super().run()
        else:
            self.flash_options.selected_kconfig = self.kconfig

    def set_previous_menu(self, previous_menu: Type[BaseMenu] | None) -> None:
        from core.menus.advanced_menu import AdvancedMenu

        self.previous_menu = (
            previous_menu if previous_menu is not None else AdvancedMenu
        )

    def set_options(self) -> None:
        if not path.isdir(self.kconfigs_dirname):
            return

        self.input_label_txt = "Select config or action to continue (default=n)"
        self.default_option = Option(
            method=self.select_config, opt_data=self.kconfig_default
        )

        self.configs = []
        option_index = 1
        for kconfig in listdir(self.kconfigs_dirname):
            if not kconfig.endswith(".config"):
                continue
            kconfig_path = path.join(self.kconfigs_dirname, kconfig)
            if path.isfile(kconfig_path):
                self.configs += [kconfig]
                self.options[str(option_index)] = Option(
                    method=self.select_config, opt_data=kconfig_path
                )
                option_index += 1
        self.options["n"] = Option(
            method=self.select_config, opt_data=self.kconfig_default
        )

    def print_menu(self) -> None:
        menu = textwrap.dedent(
            """
            ╟───────────────────────────────────────────────────────╢
            ║ Found previously saved firmware configs               ║
            ║                                                       ║
            ║ You can select existing firmware config or create a   ║
            ║ new one.                                              ║
            ║                                                       ║
            """
        )[1:]

        start_index = 1
        for i, s in enumerate(self.configs):
            line = f"{start_index + i}) {s}"
            menu += f"║ {line:<54}║\n"

        new_config = Color.apply("n) New firmware config", Color.YELLOW)
        menu += f"║ {new_config:<63}║\n"

        menu += "║                                                       ║\n"
        menu += "╟───────────────────────────────────────────────────────╢\n"

        print(menu, end="")

    def select_config(self, **kwargs) -> None:
        selection: str | None = kwargs.get("opt_data", None)
        if selection is None:
            raise Exception("opt_data is None")
        if not path.isfile(selection) and selection != self.kconfig_default:
            raise Exception("opt_data does not exists")
        self.kconfig = selection


# noinspection PyUnusedLocal
# noinspection PyMethodMayBeStatic
class KlipperBuildFirmwareMenu(BaseMenu):
    def __init__(
        self, kconfig: str | None = None, previous_menu: Type[BaseMenu] | None = None
    ):
        super().__init__()
        self.title = "Build Firmware Menu"
        self.title_color = Color.CYAN
        self.previous_menu: Type[BaseMenu] | None = previous_menu
        self.deps: Set[str] = {"build-essential", "dpkg-dev", "make"}
        self.missing_deps: List[str] = check_package_install(self.deps)
        self.flash_options = FlashOptions()
        self.kconfigs_dirname = KLIPPER_KCONFIGS_DIR
        self.kconfig_default = path.join(KLIPPER_DIR, ".config")
        self.kconfig = self.flash_options.selected_kconfig

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
        menu = textwrap.dedent(
            """
            ╟───────────────────────────────────────────────────────╢
            ║ The following dependencies are required:              ║
            ║                                                       ║
            """
        )[1:]

        for d in self.deps:
            status_ok = Color.apply("*INSTALLED*", Color.GREEN)
            status_missing = Color.apply("*MISSING*", Color.RED)
            status = status_missing if d in self.missing_deps else status_ok
            padding = 40 - len(d) + len(status) + (len(status_ok) - len(status))
            d = Color.apply(f"● {d}", Color.CYAN)
            menu += f"║ {d}{status:>{padding}} ║\n"
        menu += "║                                                       ║\n"

        color = Color.GREEN if len(self.missing_deps) == 0 else Color.RED
        txt = (
            "All dependencies are met!"
            if len(self.missing_deps) == 0
            else "Dependencies are missing!"
        )

        menu += f"║ {Color.apply(txt, color):<62} ║\n"
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
            run_make_clean(self.kconfig)
            run_make_menuconfig(self.kconfig)
            run_make(self.kconfig)

            Logger.print_ok("Firmware successfully built!")
            Logger.print_ok(f"Firmware file located in '{KLIPPER_DIR}/out'!")

            if self.kconfig == self.kconfig_default:
                self.save_firmware_config()

        except Exception as e:
            Logger.print_error(e)
            Logger.print_error("Building Klipper Firmware failed!")

        finally:
            if self.previous_menu is not None:
                self.previous_menu().run()

    def save_firmware_config(self) -> None:
        Logger.print_dialog(
            DialogType.CUSTOM,
            [
                "You can save the firmware build configs for multiple MCUs,"
                " and use them to update the firmware after a Klipper version upgrade"
            ],
            custom_title="Save firmware config",
        )
        if not get_confirm(
            "Do you want to save firmware config?", default_choice=False
        ):
            return

        filename = self.kconfig_default
        while True:
            Logger.print_dialog(
                DialogType.CUSTOM,
                [
                    "Allowed characters: a-z, 0-9 and '-'",
                    "The name must not contain the following:",
                    "\n\n",
                    "● Any special characters",
                    "● No leading or trailing '-'",
                ],
            )
            input_name = get_string_input(
                "Enter the new firmware config name",
                regex=r"^[a-z0-9]+([a-z0-9-]*[a-z0-9])?$",
            )
            filename = path.join(self.kconfigs_dirname, f"{input_name}.config")

            if path.isfile(filename):
                if get_confirm(
                    f"Firmware config {input_name} already exists, overwrite?",
                    default_choice=False,
                ):
                    break

            if path.isdir(filename):
                Logger.print_error(f"Path {filename} exists and it's a directory")

            if not path.exists(filename):
                break

        if not get_confirm(
            f"Save firmware config to '{filename}'?", default_choice=True
        ):
            Logger.print_info("Aborted saving firmware config ...")
            return

        if not path.exists(self.kconfigs_dirname):
            mkdir(self.kconfigs_dirname)

        copyfile(self.kconfig_default, filename)

        Logger.print_ok()
        Logger.print_ok(f"Firmware config successfully saved to {filename}")
