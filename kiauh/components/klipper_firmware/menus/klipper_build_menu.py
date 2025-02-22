# ======================================================================= #
#  Copyright (C) 2020 - 2025 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #
from __future__ import annotations

import textwrap
from pathlib import Path
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
        self.kconfig_default = KLIPPER_DIR.joinpath(".config")
        self.configs: List[Path] = []
        self.kconfig = (
            self.kconfig_default if not Path(self.kconfigs_dirname).is_dir() else None
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
        if not Path(self.kconfigs_dirname).is_dir():
            return

        self.input_label_txt = "Select config or action to continue (default=N)"
        self.default_option = Option(
            method=self.select_config, opt_data=self.kconfig_default
        )

        option_index = 1
        for kconfig in Path(self.kconfigs_dirname).iterdir():
            if not kconfig.name.endswith(".config"):
                continue
            kconfig_path = self.kconfigs_dirname.joinpath(kconfig)
            if Path(kconfig_path).is_file():
                self.configs += [kconfig]
                self.options[str(option_index)] = Option(
                    method=self.select_config, opt_data=kconfig_path
                )
                option_index += 1
        self.options["n"] = Option(
            method=self.select_config, opt_data=self.kconfig_default
        )

    def print_menu(self) -> None:
        cfg_found_str = Color.apply(
            "Previously saved firmware configs found!", Color.GREEN
        )
        menu = textwrap.dedent(
            f"""
            ╟───────────────────────────────────────────────────────╢
            ║ {cfg_found_str:^62} ║
            ║                                                       ║
            ║    Select an existing config or create a new one.     ║
            ╟───────────────────────────────────────────────────────╢
            ║ Available firmware configs:                           ║
            """
        )[1:]

        start_index = 1
        for i, s in enumerate(self.configs):
            line = f"{start_index + i}) {s.name}"
            menu += f"║ {line:<54}║\n"

        new_config = Color.apply("N) Create new firmware config", Color.GREEN)
        menu += "║                                                       ║\n"
        menu += f"║ {new_config:<62} ║\n"

        menu += "╟───────────────────────────────────────────────────────╢\n"

        print(menu, end="")

    def select_config(self, **kwargs) -> None:
        selection: str | None = kwargs.get("opt_data", None)
        if selection is None:
            raise Exception("opt_data is None")
        if not Path(selection).is_file() and selection != self.kconfig_default:
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
        self.kconfig_default = KLIPPER_DIR.joinpath(".config")
        self.kconfig = self.flash_options.selected_kconfig

    def set_previous_menu(self, previous_menu: Type[BaseMenu] | None) -> None:
        from core.menus.advanced_menu import AdvancedMenu

        self.previous_menu = (
            previous_menu if previous_menu is not None else AdvancedMenu
        )

    def set_options(self) -> None:
        self.input_label_txt = "Press ENTER to install dependencies"
        self.default_option = Option(method=self.install_missing_deps)

    def run(self):
        # immediately start the build process if all dependencies are met
        if len(self.missing_deps) == 0:
            self.start_build_process()
        else:
            super().run()

    def print_menu(self) -> None:
        txt = Color.apply("Dependencies are missing!", Color.RED)
        menu = textwrap.dedent(
            f"""
            ╟───────────────────────────────────────────────────────╢
            ║ {txt:^62} ║
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
            filename = self.kconfigs_dirname.joinpath(f"{input_name}.config")

            if Path(filename).is_file():
                if get_confirm(
                    f"Firmware config {input_name} already exists, overwrite?",
                    default_choice=False,
                ):
                    break

            if Path(filename).is_dir():
                Logger.print_error(f"Path {filename} exists and it's a directory")

            if not Path(filename).exists():
                break

        if not get_confirm(
            f"Save firmware config to '{filename}'?", default_choice=True
        ):
            Logger.print_info("Aborted saving firmware config ...")
            return

        if not Path(self.kconfigs_dirname).exists():
            Path(self.kconfigs_dirname).mkdir()

        copyfile(self.kconfig_default, filename)

        Logger.print_ok()
        Logger.print_ok(f"Firmware config successfully saved to {filename}")
