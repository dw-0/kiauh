# ======================================================================= #
#  Copyright (C) 2020 - 2024 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #

from subprocess import CalledProcessError, check_output, Popen, PIPE, STDOUT
from typing import List

from components.klipper import KLIPPER_DIR
from components.klipper_firmware.flash_options import FlashOptions, FlashCommand
from utils.logger import Logger
from utils.system_utils import log_process


def find_usb_device_by_id() -> List[str]:
    try:
        command = "find /dev/serial/by-id/* 2>/dev/null"
        output = check_output(command, shell=True, text=True)
        return output.splitlines()
    except CalledProcessError as e:
        Logger.print_error("Unable to find a USB device!")
        Logger.print_error(e, prefix=False)
        return []


def find_uart_device() -> List[str]:
    try:
        command = '"find /dev -maxdepth 1 -regextype posix-extended -regex "^\/dev\/tty(AMA0|S0)$" 2>/dev/null"'
        output = check_output(command, shell=True, text=True)
        return output.splitlines()
    except CalledProcessError as e:
        Logger.print_error("Unable to find a UART device!")
        Logger.print_error(e, prefix=False)
        return []


def find_usb_dfu_device() -> List[str]:
    try:
        command = '"lsusb | grep "DFU" | cut -d " " -f 6 2>/dev/null"'
        output = check_output(command, shell=True, text=True)
        return output.splitlines()
    except CalledProcessError as e:
        Logger.print_error("Unable to find a USB DFU device!")
        Logger.print_error(e, prefix=False)
        return []


def flash_device(flash_options: FlashOptions) -> None:
    try:
        if not flash_options.selected_mcu:
            raise Exception("Missing value for selected_mcu!")

        if flash_options.flash_command is FlashCommand.FLASH:
            command = [
                "make",
                flash_options.flash_command.value,
                f"FLASH_DEVICE={flash_options.selected_mcu}",
            ]
            process = Popen(
                command, cwd=KLIPPER_DIR, stdout=PIPE, stderr=STDOUT, text=True
            )

            log_process(process)

            rc = process.returncode
            if rc != 0:
                raise Exception(f"Flashing failed with returncode: {rc}")
            else:
                Logger.print_ok("Flashing successfull!", start="\n", end="\n\n")

    except (Exception, CalledProcessError):
        Logger.print_error("Flashing failed!", start="\n")
        Logger.print_error("See the console output above!", end="\n\n")
