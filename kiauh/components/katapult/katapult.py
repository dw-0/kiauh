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
from subprocess import CalledProcessError
from typing import List

from components.katapult import (
    KATAPULT_DIR,
    KATAPULT_REPO,
    # KATAPULT_FLASHTOOL # TODO: to be used when implementing flashing
)
from components.klipper.klipper import Klipper
from core.logger import DialogType, Logger
from core.types.component_status import ComponentStatus
from utils.common import get_install_status
from utils.git_utils import (
    git_clone_wrapper,
    git_pull_wrapper,
)
from utils.input_utils import get_confirm
from utils.instance_utils import get_instances

### TODO: update imports when implementing backup support
# from core.services.backup_service import BackupService
# from core.settings.kiauh_settings import KiauhSettings
# from core.types.component_status import ComponentStatus

# from utils.sys_utils import (
#     # cmd_sysctl_service,
#     # parse_packages_from_file,
# )

### TODO: update imports when implementing CAN interface check
# from utils.common import (
#     # check_install_dependencies,
#     # get_install_status,
# )


def install_katapult() -> None:
    # Step 1: Print disclaimer and get confirmation
    print_katapult_brick_warning()

    if not get_confirm("Do you want to continue with the installation?"):
        Logger.print_info("Katapult installation aborted!")
        return

    Logger.print_status("Starting the installer script for Katapult ...")
    time.sleep(1)

    # Step 2: Check for a valid CAN interface
    # TODO: implement CAN interface check

    # Step 3: Check for Multi Instance
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

    # Step 4: Clone Katapult repo
    git_clone_wrapper(KATAPULT_REPO, KATAPULT_DIR, "master")

    # Step 5: Install dependencies
    # TODO: check for python3-serial, or maybe add an interactive prompt (only used for flashing over USB/UART)


def print_katapult_brick_warning() -> None:
    Logger.print_dialog(
        DialogType.WARNING,
        [
            "Katapult is a CAN flashtool for 3D printer controllers.",
            "\n\n",
            "Please ensure you understand the risks involved in flashing "
            "firmware to your device. Improper use may lead to bricking "
            "your hardware.",
            "\n\n",
            "Proceed only if you are confident and have backed up "
            "necessary configurations. This is much riskier than flashing Klipper",
            "\n\n",
            "If unsure, seek assistance from the community. A bricked device "
            "WILL need to be recovered via an external programmer.",
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
