#!/usr/bin/env python3

# ======================================================================= #
#  Copyright (C) 2020 - 2024 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #

import shutil
import subprocess
from typing import List, Union

from kiauh.core.instance_manager.instance_manager import InstanceManager
from kiauh.modules.klipper.klipper_dialogs import print_instance_overview
from kiauh.modules.moonraker import MOONRAKER_DIR, MOONRAKER_ENV_DIR
from kiauh.modules.moonraker.moonraker import Moonraker
from kiauh.utils.filesystem_utils import remove_file
from kiauh.utils.input_utils import get_selection_input
from kiauh.utils.logger import Logger


def run_moonraker_removal(
    remove_service: bool,
    remove_dir: bool,
    remove_env: bool,
    remove_polkit: bool,
    delete_logs: bool,
) -> None:
    im = InstanceManager(Moonraker)

    if remove_service:
        Logger.print_status("Removing Moonraker instances ...")
        if im.instances:
            instances_to_remove = select_instances_to_remove(im.instances)
            remove_instances(im, instances_to_remove)
        else:
            Logger.print_info("No Moonraker Services installed! Skipped ...")

    if (remove_polkit or remove_dir or remove_env) and im.instances:
        Logger.print_warn("There are still other Moonraker services installed!")
        Logger.print_warn("Therefor the following parts cannot be removed:")
        Logger.print_warn(
            """
            ● Moonraker PolicyKit rules
            ● Moonraker local repository
            ● Moonraker Python environment
            """,
            False,
        )
    else:
        if remove_polkit:
            Logger.print_status("Removing all Moonraker policykit rules ...")
            remove_polkit_rules()
        if remove_dir:
            Logger.print_status("Removing Moonraker local repository ...")
            remove_moonraker_dir()
        if remove_env:
            Logger.print_status("Removing Moonraker Python environment ...")
            remove_moonraker_env()

    # delete moonraker logs of all instances
    if delete_logs:
        Logger.print_status("Removing all Moonraker logs ...")
        delete_moonraker_logs(im.instances)


def select_instances_to_remove(
    instances: List[Moonraker],
) -> Union[List[Moonraker], None]:
    print_instance_overview(instances, True, True)

    options = [str(i) for i in range(len(instances))]
    options.extend(["a", "A", "b", "B"])

    selection = get_selection_input("Select Moonraker instance to remove", options)

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
    instance_list: List[Moonraker],
) -> None:
    for instance in instance_list:
        Logger.print_status(f"Removing instance {instance.get_service_file_name()} ...")
        instance_manager.current_instance = instance
        instance_manager.stop_instance()
        instance_manager.disable_instance()
        instance_manager.delete_instance()

    instance_manager.reload_daemon()


def remove_moonraker_dir() -> None:
    if not MOONRAKER_DIR.exists():
        Logger.print_info(f"'{MOONRAKER_DIR}' does not exist. Skipped ...")
        return

    try:
        shutil.rmtree(MOONRAKER_DIR)
    except OSError as e:
        Logger.print_error(f"Unable to delete '{MOONRAKER_DIR}':\n{e}")


def remove_moonraker_env() -> None:
    if not MOONRAKER_ENV_DIR.exists():
        Logger.print_info(f"'{MOONRAKER_ENV_DIR}' does not exist. Skipped ...")
        return

    try:
        shutil.rmtree(MOONRAKER_ENV_DIR)
    except OSError as e:
        Logger.print_error(f"Unable to delete '{MOONRAKER_ENV_DIR}':\n{e}")


def remove_polkit_rules() -> None:
    if not MOONRAKER_DIR.exists():
        log = "Cannot remove policykit rules. Moonraker directory not found."
        Logger.print_warn(log)
        return

    try:
        command = [f"{MOONRAKER_DIR}/scripts/set-policykit-rules.sh", "--clear"]
        subprocess.run(
            command, stderr=subprocess.PIPE, stdout=subprocess.DEVNULL, check=True
        )
    except subprocess.CalledProcessError as e:
        Logger.print_error(f"Error while removing policykit rules: {e}")

    Logger.print_ok("Policykit rules successfully removed!")


def delete_moonraker_logs(instances: List[Moonraker]) -> None:
    all_logfiles = []
    for instance in instances:
        all_logfiles = list(instance.log_dir.glob("moonraker.log*"))
    if not all_logfiles:
        Logger.print_info("No Moonraker logs found. Skipped ...")
        return

    for log in all_logfiles:
        Logger.print_status(f"Remove '{log}'")
        remove_file(log)
