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

from components.katapult import (
    KATAPULT_DIR,
    KATAPULT_KCONFIGS_DIR,
    KATAPULT_REPO,
)
from components.katapult.flashtool import check_katapult_running, flash_with_flashtool
from components.klipper import KLIPPER_DIR
from components.klipper.klipper import Klipper
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

# Katapult can only flash the raw binary, not the elf/hex/uf2 build outputs
KLIPPER_FIRMWARE_BIN = KLIPPER_DIR.joinpath("out/klipper.bin")


def install_katapult() -> None:
    # step 1: print disclaimer and get confirmation
    print_katapult_brick_warning()

    if not get_confirm("Do you want to continue with the installation?"):
        Logger.print_info("Katapult installation aborted!")
        return

    Logger.print_status("Starting the installer script for Katapult ...")
    time.sleep(1)

    # step 2: check for a valid CAN interface
    # TODO add support for multiple CAN interfaces (or at least list them for the user to choose from)
    if not check_can_interface("can0"):
        Logger.print_info("Aborting Katapult installation — no CAN interface found.")
        return

    # step 3: check for Multi Instances

    # TODO Add multi instance support.
    # I believe we only need to ensure people are offered a way to choose which CAN interface to use.
    # For now, default is to block multi instance installs.
    # This should really be thought through more carefully later on,
    # as Katapult has the potential to brick devices if used improperly.

    # if len(instances) > 1:
    #     Logger.print_dialog(DialogType.INFO, ["Multiple Klipper instances found:"])
    #     for i, instance in enumerate(instances, 1):
    #         print(f"{i}. {instance.data_dir.name}")
    #     choice = input("Select instance to flash: ")
    #     selected = instances[int(choice) - 1]
    # else:
    #     selected = instances[0]
    #
    # Then we'd only need to find a way to 'assign' each interface to its corresponding instance

    instances: List[Klipper] = get_instances(Klipper)

    if len(instances) > 1:
        print_multi_instance_warning(instances)
        Logger.print_info("Katapult installation aborted!")
        return

    # step 4: clone Katapult repo
    git_clone_wrapper(KATAPULT_REPO, KATAPULT_DIR, "master")

    # step 5: install dependencies
    # TODO: check for python3-serial, or maybe add an interactive prompt (only used for flashing over USB/UART)
    # as of now, we only check for python3-serial when building, which will install it along with Katapult even if not needed.


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
    try:
        if check_katapult_running():
            Logger.print_error("Katapult's flashtool is running! Aborting update.")
            return

        if not KATAPULT_DIR.exists():
            git_clone_wrapper(KATAPULT_REPO, KATAPULT_DIR, "master")
        else:
            Logger.print_status("Updating Katapult ...")

            if get_confirm(
                "Do you want to backup the Katapult directory before updating?"
            ):
                backup_katapult_dir()

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

    if KATAPULT_KCONFIGS_DIR.exists():
        if get_confirm("Do you also want to remove the configurations directory ?"):
            shutil.rmtree(KATAPULT_KCONFIGS_DIR)
            Logger.print_ok(
                "Directory removed! Katapult configurations have been sucessfully deleted."
            )


def backup_katapult_dir() -> None:
    svc = BackupService()
    svc.backup_directory(
        source_path=KATAPULT_DIR,
        backup_name="Katapult",
        target_path="Katapult",
    )


def flash_klipper_via_katapult() -> None:
    if not KLIPPER_FIRMWARE_BIN.is_file():
        Logger.print_dialog(
            DialogType.ERROR,
            [
                f"No Klipper firmware found at '{KLIPPER_FIRMWARE_BIN}'!",
                "\n\n",
                "Build the Klipper firmware first, with a bootloader offset matching "
                "the application offset of Katapult on the MCU.",
            ],
        )
        return

    flash_with_flashtool(KLIPPER_FIRMWARE_BIN, "flashing of Klipper")


def check_can_interface(interface="can0") -> bool:
    try:
        run(
            ["ip", "link", "show", interface],
            check=True,
            capture_output=True,
        )
        return True
    except CalledProcessError:
        Logger.print_error(f"CAN interface '{interface}' not found or not up!")
        return False
