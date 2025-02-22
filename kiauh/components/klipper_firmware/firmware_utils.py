# ======================================================================= #
#  Copyright (C) 2020 - 2025 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #
import re
from pathlib import Path
from subprocess import (
    DEVNULL,
    PIPE,
    STDOUT,
    CalledProcessError,
    Popen,
    check_output,
    run,
)
from typing import List

from components.klipper import KLIPPER_DIR
from components.klipper.klipper import Klipper
from components.klipper_firmware import SD_FLASH_SCRIPT
from components.klipper_firmware.flash_options import (
    FlashMethod,
    FlashOptions,
)
from core.instance_manager.instance_manager import InstanceManager
from core.logger import Logger
from utils.instance_utils import get_instances
from utils.sys_utils import log_process


def find_firmware_file() -> bool:
    target = KLIPPER_DIR.joinpath("out")
    target_exists: bool = target.exists()

    f1 = "klipper.elf.hex"
    f2 = "klipper.elf"
    f3 = "klipper.bin"
    f4 = "klipper.uf2"
    fw_file_exists: bool = (
        (target.joinpath(f1).exists() and target.joinpath(f2).exists())
        or target.joinpath(f3).exists()
        or target.joinpath(f4).exists()
    )

    return target_exists and fw_file_exists


def find_usb_device_by_id() -> List[str]:
    try:
        command = "find /dev/serial/by-id/*"
        output = check_output(command, shell=True, text=True, stderr=DEVNULL)
        return output.splitlines()
    except CalledProcessError as e:
        Logger.print_error("Unable to find a USB device!")
        Logger.print_error(e, prefix=False)
        return []


def find_uart_device() -> List[str]:
    try:
        cmd = "find /dev -maxdepth 1"
        output = check_output(cmd, shell=True, text=True, stderr=DEVNULL)
        device_list = []
        if output:
            pattern = r"^/dev/tty(AMA0|S0)$"
            devices = output.splitlines()
            device_list = [d for d in devices if re.search(pattern, d)]
        return device_list
    except CalledProcessError as e:
        Logger.print_error("Unable to find a UART device!")
        Logger.print_error(e, prefix=False)
        return []


def find_usb_dfu_device() -> List[str]:
    try:
        output = check_output("lsusb", shell=True, text=True, stderr=DEVNULL)
        device_list = []
        if output:
            devices = output.splitlines()
            device_list = [d.split(" ")[5] for d in devices if "DFU" in d]
        return device_list

    except CalledProcessError as e:
        Logger.print_error("Unable to find a USB DFU device!")
        Logger.print_error(e, prefix=False)
        return []


def find_usb_rp2_boot_device() -> List[str]:
    try:
        output = check_output("lsusb", shell=True, text=True, stderr=DEVNULL)
        device_list = []
        if output:
            devices = output.splitlines()
            device_list = [d.split(" ")[5] for d in devices if "RP2 Boot" in d]
        return device_list

    except CalledProcessError as e:
        Logger.print_error("Unable to find a USB RP2 Boot device!")
        Logger.print_error(e, prefix=False)
        return []


def get_sd_flash_board_list() -> List[str]:
    if not KLIPPER_DIR.exists() or not SD_FLASH_SCRIPT.exists():
        return []

    try:
        cmd = f"{SD_FLASH_SCRIPT} -l"
        blist: List[str] = check_output(cmd, shell=True, text=True).splitlines()[1:]
        return blist
    except CalledProcessError as e:
        Logger.print_error(f"An unexpected error occured:\n{e}")
        return []


def start_flash_process(flash_options: FlashOptions) -> None:
    Logger.print_status(f"Flashing '{flash_options.selected_mcu}' ...")
    try:
        if not flash_options.flash_method:
            raise Exception("Missing value for flash_method!")
        if not flash_options.flash_command:
            raise Exception("Missing value for flash_command!")
        if not flash_options.selected_mcu:
            raise Exception("Missing value for selected_mcu!")
        if not flash_options.connection_type:
            raise Exception("Missing value for connection_type!")
        if (
            flash_options.flash_method == FlashMethod.SD_CARD
            and not flash_options.selected_board
        ):
            raise Exception("Missing value for selected_board!")

        if flash_options.flash_method is FlashMethod.REGULAR:
            cmd = [
                "make",
                f"KCONFIG_CONFIG={flash_options.selected_kconfig}",
                flash_options.flash_command.value,
                f"FLASH_DEVICE={flash_options.selected_mcu}",
            ]
        elif flash_options.flash_method is FlashMethod.SD_CARD:
            if not SD_FLASH_SCRIPT.exists():
                raise Exception("Unable to find Klippers sdcard flash script!")
            cmd = [
                SD_FLASH_SCRIPT.as_posix(),
                f"-b {flash_options.selected_baudrate}",
                flash_options.selected_mcu,
                flash_options.selected_board,
            ]
        else:
            raise Exception("Invalid value for flash_method!")

        instances = get_instances(Klipper)
        InstanceManager.stop_all(instances)

        process = Popen(cmd, cwd=KLIPPER_DIR, stdout=PIPE, stderr=STDOUT, text=True)
        log_process(process)

        InstanceManager.start_all(instances)

        rc = process.returncode
        if rc != 0:
            raise Exception(f"Flashing failed with returncode: {rc}")
        else:
            Logger.print_ok("Flashing successful!", start="\n", end="\n\n")

    except (Exception, CalledProcessError):
        Logger.print_error("Flashing failed!", start="\n")
        Logger.print_error("See the console output above!", end="\n\n")


def run_make_clean(kconfig=Path(KLIPPER_DIR.joinpath(".config"))) -> None:
    try:
        run(
            f"make KCONFIG_CONFIG={kconfig} clean",
            cwd=KLIPPER_DIR,
            shell=True,
            check=True,
        )
    except CalledProcessError as e:
        Logger.print_error(f"Unexpected error:\n{e}")
        raise


def run_make_menuconfig(kconfig=Path(KLIPPER_DIR.joinpath(".config"))) -> None:
    try:
        run(
            f"make PYTHON=python3 KCONFIG_CONFIG={kconfig} menuconfig",
            cwd=KLIPPER_DIR,
            shell=True,
            check=True,
        )
    except CalledProcessError as e:
        Logger.print_error(f"Unexpected error:\n{e}")
        raise


def run_make(kconfig=Path(KLIPPER_DIR.joinpath(".config"))) -> None:
    try:
        run(
            f"make PYTHON=python3 KCONFIG_CONFIG={kconfig}",
            cwd=KLIPPER_DIR,
            shell=True,
            check=True,
        )
    except CalledProcessError as e:
        Logger.print_error(f"Unexpected error:\n{e}")
        raise
