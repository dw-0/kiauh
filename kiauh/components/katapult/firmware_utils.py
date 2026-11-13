# ======================================================================= #
#  Copyright (C) 2020 - 2026 Dominik Willner <dev.dw-0@proton.me>         #
#  Copyright (C) 2026 Théo Gaillard <theo.gayar@gmail.com>                #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #
from __future__ import annotations

from enum import Enum
from pathlib import Path
from subprocess import DEVNULL, CalledProcessError, check_output, run
from typing import List, Set

from components.katapult import KATAPULT_DIR
from core.logger import Logger
from utils.common import check_install_dependencies

# USB IDs of RP2040 and RP235x MCUs in boot mode
RP2_BOOT_USB_IDS = ["2e8a:0003", "2e8a:000f"]


def install_flash_deps(deps: Set[str]) -> bool:
    """
    Install missing packages required for flashing |
    :param deps: The required system packages
    :return: True if all packages are installed, False otherwise
    """
    try:
        check_install_dependencies({*deps}, include_global=False)
        return True
    except Exception as e:
        Logger.print_error(f"Installing the flashing dependencies failed!\n{e}")
        return False


class KatapultArch(Enum):
    STM32 = "CONFIG_MACH_STM32"
    RP2 = "CONFIG_MACH_RPXXXX"
    LPC176X = "CONFIG_MACH_LPC176X"


def get_kconfig_arch(kconfig: Path) -> KatapultArch | None:
    """
    Read the MCU architecture from a Katapult build config |
    :param kconfig: The Katapult build config
    :return: The configured architecture, or None if it can't be determined
    """
    try:
        lines = kconfig.read_text().splitlines()
    except OSError:
        return None
    for arch in KatapultArch:
        if f"{arch.value}=y" in lines:
            return arch
    return None


def find_usb_rp2_boot_devices() -> List[str]:
    try:
        output = check_output(["lsusb"], text=True, stderr=DEVNULL)
    except (CalledProcessError, OSError):
        return []
    return [
        usb_id
        for line in output.splitlines()
        for usb_id in RP2_BOOT_USB_IDS
        if f" ID {usb_id} " in f"{line} "
    ]


def run_make_flash(kconfig: Path, flash_device: str | None = None) -> None:
    """
    Rebuild Katapult from scratch with the given config and flash it with
    `make flash`, which uses dfu-util for STM32 and rp2040_flash for RP2 MCUs |
    :param kconfig: The Katapult build config
    :param flash_device: The USB ID of the STM32 DFU device, unused for RP2 MCUs
    :return: None
    """
    # always do a clean build, so a stale build of another config can't be flashed
    run_make_clean(kconfig)
    cmd = ["make", "PYTHON=python3", f"KCONFIG_CONFIG={kconfig}", "flash"]
    if flash_device is not None:
        cmd.append(f"FLASH_DEVICE={flash_device}")
    run(cmd, cwd=KATAPULT_DIR, check=True)


def run_make_clean(kconfig=Path(KATAPULT_DIR.joinpath(".config"))) -> None:
    try:
        run(
            f"make KCONFIG_CONFIG={kconfig} clean",
            cwd=KATAPULT_DIR,
            shell=True,
            check=True,
        )
    except CalledProcessError as e:
        Logger.print_error(f"Unexpected error:\n{e}")
        raise


def run_make_menuconfig(kconfig=Path(KATAPULT_DIR.joinpath(".config"))) -> None:
    try:
        run(
            f"make PYTHON=python3 KCONFIG_CONFIG={kconfig} menuconfig",
            cwd=KATAPULT_DIR,
            shell=True,
            check=True,
        )
    except CalledProcessError as e:
        Logger.print_error(f"Unexpected error:\n{e}")
        raise


def run_make(kconfig=Path(KATAPULT_DIR.joinpath(".config"))) -> None:
    try:
        run(
            f"make PYTHON=python3 KCONFIG_CONFIG={kconfig}",
            cwd=KATAPULT_DIR,
            shell=True,
            check=True,
        )
    except CalledProcessError as e:
        Logger.print_error(f"Unexpected error:\n{e}")
        raise
