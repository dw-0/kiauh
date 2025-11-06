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

import psutil
from components.katapult import KATAPULT_DIR, KATAPULT_FLASHTOOL_PATH, KATAPULT_REPO
from components.katapult.firmware_utils import (
    find_firmware_file,
    find_uart_device,
)
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
from utils.input_utils import (
    get_confirm,
    get_number_input,
    get_selection_input,
    get_string_input,
)
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
    if not check_can_interface("can0"):
        Logger.print_info("Aborting Katapult installation — no CAN interface found.")
        return

    # step 3: check for Multi Instances

    # TODO Add multi instance support. I believe we only need to ensure people
    # are offered a way to choose which CAN interface to use.
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

    instances = get_instances(Klipper)

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

# def flash_klipper_via_katapult() -> None:
#     raise NotImplementedError("Feature not yet implemented")


def flash_klipper_via_katapult() -> None:
    # step 1: stop all instances
    stop_all_klipper_instances()

    # step 2: check there is a valid Klipper bin file to flash
    if not find_firmware_file():
        restart_all_klipper_instances()
        raise Exception("No firmware file found in /klipper/out")
    # TODO add a better dialog, such as the one in katapult_flash_error_menu

    # step 3 : enter the bootloader mode on the target device flashtool.py --request-bootloader
    # First, check there is only one node on the network
    # NOTE: A query should only be performed when a single can node is on the network. Attempting to query multiple nodes may result in transmission errors that can force a node into a "bus off" state. When a node enters "bus off" it becomes unresponsive. The node must be reset to recover.

    # Then proceed
    try:
        run(
            f"python3 {KATAPULT_FLASHTOOL_PATH} --request-bootloader",
            cwd=KATAPULT_DIR,
            shell=True,
            check=True,
        )
    except CalledProcessError as e:
        restart_all_klipper_instances()
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
    # Ask user whether to flash via CAN or Serial
    Logger.print_status("Select flashing transport for Klipper (CAN or Serial) ...")

    choice = get_selection_input(
        question="Select transport: 1) CAN  2) Serial (default= CAN)",
        option_list={"1": "CAN", "2": "Serial"},
        default="1",
    )

    # check katapult not already running
    if check_katapult_running():
        restart_all_klipper_instances()
        raise Exception("An instance of Katapult is already running! Aborting...")

    if choice == "1":
        # CAN flash
        interface = get_string_input(
            question="Enter CAN interface, or hit enter to use default (can0)",
            default="can0",
            allow_special_chars=True,
            allow_empty=True,
        )

        uuid = get_string_input(
            question=("Enter UUID of target node to flash (copy from 'Query UUID')"),
            allow_empty=False,
        )

        try:
            run(
                f"python3 {KATAPULT_FLASHTOOL_PATH} --firmware {KLIPPER_DIR}/out --interface {interface} --uuid {uuid}",
                cwd=KATAPULT_DIR,
                shell=True,
                check=True,
            )
        except CalledProcessError as e:
            restart_all_klipper_instances()
            Logger.print_error(f"Unexpected error:\n{e}")
            raise

    else:
        # Serial (UART/USB) flash
        # Try to auto-detect UART devices first
        devices = find_uart_device()
        serial_device: str | None = None

        if devices:
            Logger.print_ok("Detected UART devices:", prefix=False)
            for i, d in enumerate(devices):
                print(f"  {i}) {d}")

                idx = get_number_input(
                    question="Select serial device index",
                    min_value=0,
                    max_value=len(devices) - 1,
                    allow_go_back=False,
                )
                if idx is None:
                    raise Exception("No serial device selected")
                serial_device = devices[int(idx)]
        else:
            serial_device = get_string_input(
                question="Enter serial device path (e.g. /dev/ttyUSB0)",
                allow_special_chars=True,
                allow_empty=False,
            )

        baud_rate = get_number_input(
            question="Please set the baud rate, if you are not sure, use the default (250000)",
            default=250000,
            min_value=9600,
        )

        try:
            run(
                f"python3 {KATAPULT_FLASHTOOL_PATH} --firmware {KLIPPER_DIR}/out --device {serial_device} --baud {baud_rate}",
                cwd=KATAPULT_DIR,
                shell=True,
                check=True,
            )
        except CalledProcessError as e:
            restart_all_klipper_instances()
            Logger.print_error(f"Unexpected error:\n{e}")
            raise

    # step 5: Restart Klipper
    # Logger.print_status(f"Restarting all {Klipper.__name__} instances ...")
    # InstanceManager.start_all(instances)
    restart_all_klipper_instances()


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


# TODO Maybe there is a better way to do this using a helper ? Couldn't find it
def check_katapult_running() -> bool:
    for proc in psutil.process_iter(attrs=["cmdline"]):
        cmd = " ".join(proc.info["cmdline"])
        if "katapult" in cmd and "flashtool.py" in cmd:
            Logger.print_error("Katapult flashing process detected! Aborting update.")
            return True
    return False


def stop_all_klipper_instances() -> None:
    Logger.print_status(f"Stopping all {Klipper.__name__} instances ...")
    instances = get_instances(Klipper)
    InstanceManager.stop_all(instances)


def restart_all_klipper_instances() -> None:
    Logger.print_status(f"Restarting all {Klipper.__name__} instances ...")
    instances = get_instances(Klipper)
    InstanceManager.start_all(instances)
