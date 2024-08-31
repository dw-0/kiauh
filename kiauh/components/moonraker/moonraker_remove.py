# ======================================================================= #
#  Copyright (C) 2020 - 2024 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #
from __future__ import annotations

from subprocess import DEVNULL, PIPE, CalledProcessError, run
from typing import List

from components.klipper.klipper_dialogs import print_instance_overview
from components.moonraker import MOONRAKER_DIR, MOONRAKER_ENV_DIR
from components.moonraker.moonraker import Moonraker
from core.instance_manager.instance_manager import InstanceManager
from core.logger import Logger
from utils.fs_utils import run_remove_routines
from utils.input_utils import get_selection_input
from utils.instance_utils import get_instances
from utils.sys_utils import unit_file_exists


def run_moonraker_removal(
    remove_service: bool,
    remove_dir: bool,
    remove_env: bool,
    remove_polkit: bool,
) -> None:
    instances = get_instances(Moonraker)

    if remove_service:
        Logger.print_status("Removing Moonraker instances ...")
        if instances:
            instances_to_remove = select_instances_to_remove(instances)
            remove_instances(instances_to_remove)
        else:
            Logger.print_info("No Moonraker Services installed! Skipped ...")

    delete_remaining: bool = remove_polkit or remove_dir or remove_env
    if delete_remaining and unit_file_exists("moonraker", suffix="service"):
        Logger.print_info("There are still other Moonraker services installed")
        Logger.print_info(
            "●  Moonraker PolicyKit rules were not removed.", prefix=False
        )
        Logger.print_info(f"● '{MOONRAKER_DIR}' was not removed.", prefix=False)
        Logger.print_info(f"● '{MOONRAKER_ENV_DIR}' was not removed.", prefix=False)
    else:
        if remove_polkit:
            Logger.print_status("Removing all Moonraker policykit rules ...")
            remove_polkit_rules()
        if remove_dir:
            Logger.print_status("Removing Moonraker local repository ...")
            run_remove_routines(MOONRAKER_DIR)
        if remove_env:
            Logger.print_status("Removing Moonraker Python environment ...")
            run_remove_routines(MOONRAKER_ENV_DIR)


def select_instances_to_remove(
    instances: List[Moonraker],
) -> List[Moonraker] | None:
    start_index = 1
    options = [str(i + start_index) for i in range(len(instances))]
    options.extend(["a", "b"])
    instance_map = {options[i]: instances[i] for i in range(len(instances))}

    print_instance_overview(
        instances,
        start_index=start_index,
        show_index=True,
        show_select_all=True,
    )
    selection = get_selection_input("Select Moonraker instance to remove", options)

    instances_to_remove = []
    if selection == "b":
        return None
    elif selection == "a":
        instances_to_remove.extend(instances)
    else:
        instances_to_remove.append(instance_map[selection])

    return instances_to_remove


def remove_instances(
    instance_list: List[Moonraker] | None,
) -> None:
    if not instance_list:
        Logger.print_info("No Moonraker instances found. Skipped ...")
        return
    for instance in instance_list:
        Logger.print_status(f"Removing instance {instance.service_file_path.stem} ...")
        InstanceManager.remove(instance)


def remove_polkit_rules() -> None:
    if not MOONRAKER_DIR.exists():
        log = "Cannot remove policykit rules. Moonraker directory not found."
        Logger.print_warn(log)
        return

    try:
        cmd = [f"{MOONRAKER_DIR}/scripts/set-policykit-rules.sh", "--clear"]
        run(cmd, stderr=PIPE, stdout=DEVNULL, check=True)
    except CalledProcessError as e:
        Logger.print_error(f"Error while removing policykit rules: {e}")

    Logger.print_ok("Policykit rules successfully removed!")


def delete_moonraker_logs(instances: List[Moonraker]) -> None:
    all_logfiles = []
    for instance in instances:
        all_logfiles = list(instance.base.log_dir.glob("moonraker.log*"))
    if not all_logfiles:
        Logger.print_info("No Moonraker logs found. Skipped ...")
        return

    for log in all_logfiles:
        Logger.print_status(f"Remove '{log}'")
        run_remove_routines(log)
