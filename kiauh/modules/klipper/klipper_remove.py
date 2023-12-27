#!/usr/bin/env python3

# ======================================================================= #
#  Copyright (C) 2020 - 2023 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #

import shutil
from typing import List, Union

from kiauh.core.instance_manager.instance_manager import InstanceManager
from kiauh.modules.klipper import KLIPPER_DIR, KLIPPER_ENV_DIR
from kiauh.modules.klipper.klipper import Klipper
from kiauh.modules.klipper.klipper_dialogs import print_instance_overview
from kiauh.utils.filesystem_utils import remove_file
from kiauh.utils.input_utils import get_selection_input
from kiauh.utils.logger import Logger


def run_klipper_removal(
    remove_service: bool,
    remove_dir: bool,
    remove_env: bool,
    delete_logs: bool,
) -> None:
    im = InstanceManager(Klipper)

    if remove_service:
        Logger.print_status("Removing Klipper instances ...")
        if im.instances:
            instances_to_remove = select_instances_to_remove(im.instances)
            remove_instances(im, instances_to_remove)
        else:
            Logger.print_info("No Klipper Services installed! Skipped ...")

    if (remove_dir or remove_env) and im.instances:
        Logger.print_warn("There are still other Klipper services installed!")
        Logger.print_warn("Therefor the following parts cannot be removed:")
        Logger.print_warn(
            """
            ● Klipper local repository
            ● Klipper Python environment
            """,
            False,
        )
    else:
        if remove_dir:
            Logger.print_status("Removing Klipper local repository ...")
            remove_klipper_dir()
        if remove_env:
            Logger.print_status("Removing Klipper Python environment ...")
            remove_klipper_env()

    # delete klipper logs of all instances
    if delete_logs:
        Logger.print_status("Removing all Klipper logs ...")
        delete_klipper_logs(im.instances)


def select_instances_to_remove(
    instances: List[Klipper],
) -> Union[List[Klipper], None]:
    print_instance_overview(instances, True, True)

    options = [str(i) for i in range(len(instances))]
    options.extend(["a", "A", "b", "B"])

    selection = get_selection_input("Select Klipper instance to remove", options)

    instances_to_remove = []
    if selection == "b".lower():
        return None
    elif selection == "a".lower():
        instances_to_remove.extend(instances)
    else:
        instance = instances[int(selection)]
        instances_to_remove.append(instance)

    return instances_to_remove


def remove_instances(
    instance_manager: InstanceManager,
    instance_list: List[Klipper],
) -> None:
    for instance in instance_list:
        Logger.print_status(f"Removing instance {instance.get_service_file_name()} ...")
        instance_manager.current_instance = instance
        instance_manager.stop_instance()
        instance_manager.disable_instance()
        instance_manager.delete_instance()

    instance_manager.reload_daemon()


def remove_klipper_dir() -> None:
    if not KLIPPER_DIR.exists():
        Logger.print_info(f"'{KLIPPER_DIR}' does not exist. Skipped ...")
        return

    try:
        shutil.rmtree(KLIPPER_DIR)
    except OSError as e:
        Logger.print_error(f"Unable to delete '{KLIPPER_DIR}':\n{e}")


def remove_klipper_env() -> None:
    if not KLIPPER_ENV_DIR.exists():
        Logger.print_info(f"'{KLIPPER_ENV_DIR}' does not exist. Skipped ...")
        return

    try:
        shutil.rmtree(KLIPPER_ENV_DIR)
    except OSError as e:
        Logger.print_error(f"Unable to delete '{KLIPPER_ENV_DIR}':\n{e}")


def delete_klipper_logs(instances: List[Klipper]) -> None:
    all_logfiles = []
    for instance in instances:
        all_logfiles = list(instance.log_dir.glob("klippy.log*"))
    if not all_logfiles:
        Logger.print_info("No Klipper logs found. Skipped ...")
        return

    for log in all_logfiles:
        Logger.print_status(f"Remove '{log}'")
        remove_file(log)
