# ======================================================================= #
#  Copyright (C) 2020 - 2024 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #

from typing import List, Union

from components.klipper import KLIPPER_DIR, KLIPPER_ENV_DIR
from components.klipper.klipper import Klipper
from components.klipper.klipper_dialogs import print_instance_overview
from core.instance_manager.instance_manager import InstanceManager
from utils.fs_utils import run_remove_routines
from utils.input_utils import get_selection_input
from utils.logger import Logger
from utils.sys_utils import cmd_sysctl_manage


def run_klipper_removal(
    remove_service: bool,
    remove_dir: bool,
    remove_env: bool,
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
        Logger.print_info("There are still other Klipper services installed:")
        Logger.print_info(f"● '{KLIPPER_DIR}' was not removed.", prefix=False)
        Logger.print_info(f"● '{KLIPPER_ENV_DIR}' was not removed.", prefix=False)
    else:
        if remove_dir:
            Logger.print_status("Removing Klipper local repository ...")
            run_remove_routines(KLIPPER_DIR)
        if remove_env:
            Logger.print_status("Removing Klipper Python environment ...")
            run_remove_routines(KLIPPER_ENV_DIR)


def select_instances_to_remove(
    instances: List[Klipper],
) -> Union[List[Klipper], None]:
    start_index = 1
    options = [str(i + start_index) for i in range(len(instances))]
    options.extend(["a", "A", "b", "B"])
    instance_map = {options[i]: instances[i] for i in range(len(instances))}

    print_instance_overview(
        instances,
        start_index=start_index,
        show_index=True,
        show_select_all=True,
    )
    selection = get_selection_input("Select Klipper instance to remove", options)

    instances_to_remove = []
    if selection == "b".lower():
        return None
    elif selection == "a".lower():
        instances_to_remove.extend(instances)
    else:
        instances_to_remove.append(instance_map[selection])

    return instances_to_remove


def remove_instances(
    instance_manager: InstanceManager,
    instance_list: List[Klipper],
) -> None:
    if not instance_list:
        return

    for instance in instance_list:
        Logger.print_status(f"Removing instance {instance.get_service_file_name()} ...")
        instance_manager.current_instance = instance
        instance_manager.stop_instance()
        instance_manager.disable_instance()
        instance_manager.delete_instance()

    cmd_sysctl_manage("daemon-reload")


def delete_klipper_logs(instances: List[Klipper]) -> None:
    all_logfiles = []
    for instance in instances:
        all_logfiles = list(instance.log_dir.glob("klippy.log*"))
    if not all_logfiles:
        Logger.print_info("No Klipper logs found. Skipped ...")
        return

    for log in all_logfiles:
        Logger.print_status(f"Remove '{log}'")
        run_remove_routines(log)
