# ======================================================================= #
#  Copyright (C) 2020 - 2025 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #
from __future__ import annotations

import shutil
import time
from subprocess import CalledProcessError, run
from typing import List

from components.katapult import KATAPULT_DIR, KATAPULT_FLASHTOOL_PATH, KATAPULT_REPO
from components.katapult.firmware_utils import find_firmware_file
from components.klipper import KLIPPER_DIR
from components.klipper.klipper import Klipper
from core.instance_manager.instance_manager import InstanceManager
from core.logger import DialogType, Logger
from core.services.backup_service import BackupService
from core.types.component_status import ComponentStatus
from utils.common import get_install_status
from utils.git_utils import (
    git_clone_wrapper,
    git_pull_wrapper,
)
from utils.input_utils import get_confirm
from utils.instance_utils import get_instances

### TODO: update imports when implementing CAN interface check
# from utils.common import (
#     # check_install_dependencies,
#     # get_install_status,
# )


def install_katapult() -> None:
    # step 1: print disclaimer and get confirmation
    print_katapult_brick_warning()

    if not get_confirm("Do you want to continue with the installation?"):
        Logger.print_info("Katapult installation aborted!")
        return

    Logger.print_status("Starting the installer script for Katapult ...")
    time.sleep(1)

    # step 2: check for a valid CAN interface
    # TODO: implement CAN interface check

    # step 3: check for Multi Instance
    #
    # TODO Add multi instance support. I believe we only need to ensure people
    # are offered a way to choose which CAN interface to use.
    # For now, default is to block multi instance installs.
    # This should really be thought through more carefully later on,
    # as Katapult has the potential to brick devices if used improperly.

    instances: List[Klipper] = get_instances(Klipper)

    if len(instances) > 1:
        print_multi_instance_warning(instances)
        Logger.print_info("Katapult installation aborted!")
        return

    # step 4: clone Katapult repo
    git_clone_wrapper(KATAPULT_REPO, KATAPULT_DIR, "master")

    # step 5: install dependencies
    # TODO: check for python3-serial, or maybe add an interactive prompt (only used for flashing over USB/UART)
    # dependencies are actually check for only at flash time, which is a better alternative


def print_katapult_brick_warning() -> None:
    Logger.print_dialog(
        DialogType.WARNING,
        [
            "CRITICAL WARNING — PROCEED AT YOUR OWN RISK",
            "\n\n",
            "Katapult is a low-level CAN bootloader and flashtool for 3D printer "
            "controllers. It writes directly to your device’s firmware memory, and "
            "improper use can permanently disable or 'brick' your hardware.",
            "\n\n",
            "Proceed only if you fully understand the flashing process, have verified "
            "your firmware and configuration, and backed up all necessary data. "
            "Flashing the deployer is far riskier than flashing standard firmware "
            "such as Klipper.",
            "\n\n",
            "If you are unsure, stop immediately and seek help from experienced "
            "community members. A bricked device WILL require recovery using an "
            "external programmer.",
            "\n\n",
            "DISCLAIMER: The developers and maintainers of KIAUH assume no "
            "responsibility for any damage, data loss, harm, or hardware failure "
            "resulting from use or misuse of this tool. You use Katapult and KIAUH "
            "entirely at your own risk.",
        ],
    )


def print_multi_instance_warning(instances: List[Klipper]) -> None:
    Logger.print_dialog(
        DialogType.WARNING,
        [
            "Multi instance install detected!",
            "\n\n",
            "Katapult is NOT designed to support multi instances. There is currently "
            "no support whatsoever for this. If you are interested in this feature "
            "being added, please open an issue on GitHub.",
            "\n\n",
            "The following instances were found:",
            *[f"● {instance.data_dir.name}" for instance in instances],
        ],
    )


def update_katapult() -> None:
    ### TODO Check if katapult updating works as intended
    try:
        ### TODO : check if there is a PID for an instance of Katapult and abort if so
        # cmd_sysctl_service(CROWSNEST_SERVICE_NAME, "stop")

        if not KATAPULT_DIR.exists():
            git_clone_wrapper(KATAPULT_REPO, KATAPULT_DIR, "master")
        else:
            Logger.print_status("Updating Katapult ...")

            ### TODO : backup katapult dir
            # settings = KiauhSettings()
            # if settings.kiauh.backup_before_update:
            #     svc = BackupService()
            #     svc.backup_directory(
            #         source_path=KATAPULT_DIR,
            #         target_path="katapult",
            #         backup_name="katapult",
            #     )

            git_pull_wrapper(KATAPULT_DIR)

        Logger.print_ok("Katapult updated successfully.", end="\n\n")
    except CalledProcessError as e:
        Logger.print_error(f"Something went wrong! Please try again...\n{e}")
        return


def get_katapult_status() -> ComponentStatus:
    return get_install_status(KATAPULT_DIR)


def remove_katapult() -> None:
    if not KATAPULT_DIR.exists():
        Logger.print_info("Katapult does not seem to be installed! Skipping ...")
        return

    Logger.print_status("Removing katapult directory ...")
    shutil.rmtree(KATAPULT_DIR)
    Logger.print_ok("Directory removed! Katapult has been sucessfully uninstalled.")

    # TODO add option to remove kconfigs dir as well


def backup_katapult_dir() -> None:
    svc = BackupService()
    svc.backup_directory(
        source_path=KATAPULT_DIR,
        backup_name="Katapult",
        target_path="Katapult",
    )


# TODO implement flashing Klipper using Katapult


def flash_klipper_via_katapult() -> None:
    # step 1: stop all instances
    Logger.print_status(f"Stopping all {Klipper.__name__} instances ...")
    instances = get_instances(Klipper)
    InstanceManager.stop_all(instances)

    # step 2: check there is a valid Klipper bin file to flash
    if not find_firmware_file():
        raise Exception("No firmware file found in /klipper/out")
    # TODO add a better dialog, such as the one in katapult_flash_error_menu

    # step 3 : enter the bootloader mode on the target device flashtool.py --request-bootloader
    try:
        run(
            f"python3 {KATAPULT_FLASHTOOL_PATH} --request-bootloader",
            cwd=KATAPULT_DIR,
            shell=True,
            check=True,
        )
    except CalledProcessError as e:
        Logger.print_error(f"Unexpected error:\n{e}")
        raise

    # step 4 : run the flash script
    # python3 flashtool.py -i can0 -f ~/klipper/out/klipper.bin -u <uuid>
    # or if usb
    # python3 flashtool.py -d <serial device> -b <baud_rate>

    # TODO pass can interface number as a parameter
    # TODO add a menu to select query and confirm for the uuid
    # TODO add a menu to select status and print the report (or log it anyway)
    # TODO implement a switch or if/else in order to choose from can or serial
    try:
        run(
            f"python3 {KATAPULT_FLASHTOOL_PATH} --firmware {KLIPPER_DIR}/out --interface can0 --uuid {UUID}",
            cwd=KATAPULT_DIR,
            shell=True,
            check=True,
        )
    except CalledProcessError as e:
        Logger.print_error(f"Unexpected error:\n{e}")
        raise

    # TODO Implement BaudRate Specification
    try:
        run(
            f"python3 {KATAPULT_FLASHTOOL_PATH} --firmware {KLIPPER_DIR}/out --device {SerialDevice} --baud {BaudRate}",
            cwd=KATAPULT_DIR,
            shell=True,
            check=True,
        )
    except CalledProcessError as e:
        Logger.print_error(f"Unexpected error:\n{e}")
        raise

    # step 5: Restart Klipper
    Logger.print_status(f"Restarting all {Klipper.__name__} instances ...")
    InstanceManager.start_all(instances)


