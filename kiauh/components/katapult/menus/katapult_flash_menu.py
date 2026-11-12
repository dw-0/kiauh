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
from subprocess import CalledProcessError
from typing import List, Type

from components.katapult import (
    KATAPULT_BIN,
    KATAPULT_DEPLOYER_BIN,
    KATAPULT_FLASHTOOL_PATH,
    KATAPULT_UF2,
)
from components.katapult.firmware_utils import (
    KatapultArch,
    find_usb_rp2_boot_devices,
    get_kconfig_arch,
    run_make_flash,
)
from components.katapult.flashtool import flash_with_flashtool
from components.katapult.menus.katapult_build_menu import KatapultKConfigMenu
from components.katapult.menus.katapult_flash_help_menu import (
    KatapultFlashMethodHelpMenu,
)
from components.klipper_firmware.firmware_utils import find_usb_dfu_device
from components.klipper_firmware.flash_options import FlashOptions
from core.logger import DialogType, Logger
from core.menus import FooterType, Option
from core.menus.base_menu import BaseMenu, MenuTitleStyle
from core.types.color import Color
from utils.input_utils import get_confirm, get_number_input
from utils.sys_utils import (
    check_package_install,
    install_system_packages,
    update_system_package_lists,
)

FLASH_DEPS = {
    KatapultArch.STM32: {"dfu-util"},
    # required to build rp2040_flash
    KatapultArch.RP2: {"libusb-1.0-0-dev", "pkg-config"},
}


# noinspection PyUnusedLocal
# noinspection PyMethodMayBeStatic
class KatapultFlashMethodMenu(BaseMenu):
    def __init__(self, previous_menu: Type[BaseMenu] | None = None):
        super().__init__()
        self.title = "Flash Katapult Menu"
        self.title_color = Color.CYAN
        self.help_menu = KatapultFlashMethodHelpMenu
        self.input_label_txt = "Select flash method"
        self.footer_type = FooterType.BACK_HELP

    def set_previous_menu(self, previous_menu: Type[BaseMenu] | None) -> None:
        from core.menus.advanced_menu import AdvancedMenu

        self.previous_menu = (
            previous_menu if previous_menu is not None else AdvancedMenu
        )

    def set_options(self) -> None:
        self.options = {
            "1": Option(self.flash_directly),
            "2": Option(self.update_through_katapult),
            "3": Option(self.flash_through_other_bootloader),
        }

    def print_menu(self) -> None:
        line1 = Color.apply("Flashing a Katapult build with wrong settings", Color.RED)
        line2 = Color.apply(
            "can brick the MCU! Double-check the build config", Color.RED
        )
        line3 = Color.apply("and have a recovery method at hand.", Color.RED)
        menu = textwrap.dedent(
            f"""
            ╟───────────────────────────────────────────────────────╢
            ║ How should Katapult be flashed to the MCU?            ║
            ║                                                       ║
            ║ {line1:<62} ║
            ║ {line2:<62} ║
            ║ {line3:<62} ║
            ╟───────────────────────────────────────────────────────╢
            ║ 1) Directly (STM32 DFU mode / RP2040 boot mode)       ║
            ║ 2) Update through Katapult (deployer)                 ║
            ║ 3) Through another bootloader (deployer)              ║
            ╟───────────────────────────────────────────────────────╢
            """
        )[1:]
        print(menu, end="")

    def flash_directly(self, **kwargs) -> None:
        KatapultKConfigMenu().run()
        kconfig = Path(FlashOptions().selected_kconfig)
        arch = get_kconfig_arch(kconfig)

        if arch is KatapultArch.STM32:
            build_output = KATAPULT_BIN
        elif arch is KatapultArch.RP2:
            build_output = KATAPULT_UF2
        else:
            Logger.print_dialog(
                DialogType.ERROR,
                [
                    f"Katapult can't be flashed directly with the config '{kconfig}'.",
                    "\n\n",
                    "Only STM32 MCUs in DFU mode and RP2040/RP235x MCUs in boot "
                    "mode are supported. Build Katapult first, or flash it with a "
                    "programmer or through the deployer.",
                ],
            )
            return

        if not install_flash_deps(arch):
            return

        flash_device = select_flash_device(arch)
        if flash_device is None:
            return

        Logger.print_dialog(
            DialogType.ATTENTION,
            [
                f"Config: {kconfig}",
                f"Device: {flash_device}",
                "\n\n",
                f"Katapult will be rebuilt from scratch and '{build_output.name}' "
                "will be flashed to the device.",
            ],
        )
        if not get_confirm("Start flashing?", default_choice=False):
            Logger.print_info("Flashing of Katapult aborted!")
            return

        try:
            run_make_flash(
                kconfig, flash_device if arch is KatapultArch.STM32 else None
            )
            Logger.print_ok("Flashing successful!", start="\n", end="\n\n")
        except CalledProcessError:
            Logger.print_error("Flashing failed! See the output above.")

    def update_through_katapult(self, **kwargs) -> None:
        if not check_deployer_built():
            return
        flash_with_flashtool(KATAPULT_DEPLOYER_BIN, "update of Katapult")

    def flash_through_other_bootloader(self, **kwargs) -> None:
        if not check_deployer_built():
            return
        KatapultDeployerInstructionsMenu(previous_menu=self.__class__).run()


# noinspection PyUnusedLocal
# noinspection PyMethodMayBeStatic
class KatapultDeployerInstructionsMenu(BaseMenu):
    def __init__(self, previous_menu: Type[BaseMenu] | None = None):
        super().__init__()
        self.title = "Flash the Katapult deployer"
        self.title_color = Color.CYAN
        self.title_style = MenuTitleStyle.PLAIN
        self.previous_menu: Type[BaseMenu] | None = previous_menu
        self.footer_type = FooterType.BLANK
        self.input_label_txt = "Press ENTER to go back"

    def set_previous_menu(self, previous_menu: Type[BaseMenu] | None) -> None:
        self.previous_menu = (
            previous_menu if previous_menu is not None else KatapultFlashMethodMenu
        )

    def set_options(self) -> None:
        self.default_option = Option(method=self.go_back)

    def print_menu(self) -> None:
        deployer = Color.apply("~/katapult/out/deployer.bin", Color.CYAN)
        menu = textwrap.dedent(
            f"""
            ╟───────────────────────────────────────────────────────╢
            ║ Flash the deployer with the existing bootloader of    ║
            ║ the MCU, as you would flash Klipper with it:          ║
            ║ ● {deployer:<60} ║
            ║                                                       ║
            ║ For SD card bootloaders, copy the deployer to the SD  ║
            ║ card under the name the bootloader expects (usually   ║
            ║ 'firmware.bin'), then power cycle the board.          ║
            ║                                                       ║
            ║ The deployer replaces the existing bootloader with    ║
            ║ Katapult, then starts Katapult. Flash Klipper again   ║
            ║ afterwards, built for Katapult's application offset.  ║
            ╟───────────────────────────────────────────────────────╢
            """
        )[1:]
        print(menu, end="")

    def go_back(self, **kwargs) -> None:
        if self.previous_menu is not None:
            self.previous_menu().run()


def check_deployer_built() -> bool:
    if not KATAPULT_FLASHTOOL_PATH.is_file():
        Logger.print_error("Katapult is not installed! Install it first.")
        return False
    if not KATAPULT_DEPLOYER_BIN.is_file():
        Logger.print_dialog(
            DialogType.ERROR,
            [
                f"No deployer found at '{KATAPULT_DEPLOYER_BIN}'!",
                "\n\n",
                "Build Katapult with the 'Build Katapult deployment application' "
                "option set to the offset of the MCU's current bootloader.",
            ],
        )
        return False
    return True


def install_flash_deps(arch: KatapultArch) -> bool:
    missing_deps = check_package_install(FLASH_DEPS[arch])
    if not missing_deps:
        return True

    Logger.print_dialog(
        DialogType.ATTENTION,
        [
            "Flashing Katapult requires the following packages:",
            *[f"● {dep}" for dep in missing_deps],
        ],
    )
    if not get_confirm("Install the missing packages now?"):
        Logger.print_info("Flashing of Katapult aborted!")
        return False

    try:
        update_system_package_lists(silent=False)
        install_system_packages(missing_deps)
        return True
    except Exception as e:
        Logger.print_error(f"Installing the dependencies failed!\n{e}")
        return False


def select_flash_device(arch: KatapultArch) -> str | None:
    if arch is KatapultArch.STM32:
        devices: List[str] = find_usb_dfu_device()
        mode = "DFU mode"
    else:
        devices = find_usb_rp2_boot_devices()
        mode = "boot mode"

    if not devices:
        Logger.print_error(f"No MCU in {mode} found!")
        Logger.print_error(f"Put the MCU in {mode} and try again.", prefix=False)
        return None
    if len(devices) == 1:
        return devices[0]
    if arch is KatapultArch.RP2:
        # rp2040_flash always flashes the first device it finds
        Logger.print_error(f"Found {len(devices)} MCUs in {mode}!")
        Logger.print_error("Only connect the MCU to flash.", prefix=False)
        return None

    Logger.print_dialog(
        DialogType.CUSTOM,
        [f"{i}) {device}" for i, device in enumerate(devices, 1)],
        custom_title=f"MCUs in {mode}",
    )
    index = get_number_input(
        "Select MCU to flash (b=back)",
        min_value=1,
        max_value=len(devices),
        allow_go_back=True,
    )
    return devices[index - 1] if index is not None else None
