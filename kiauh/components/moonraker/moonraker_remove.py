# ======================================================================= #
#  Copyright (C) 2020 - 2024 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #

from subprocess import DEVNULL, PIPE, CalledProcessError, run
from typing import List, Union

from components.klipper.klipper_dialogs import print_instance_overview
from components.moonraker import MOONRAKER_DIR, MOONRAKER_ENV_DIR
from components.moonraker.moonraker import Moonraker
from core.instance_manager.instance_manager import InstanceManager
from utils.fs_utils import run_remove_routines
from utils.input_utils import get_selection_input
from utils.logger import Logger
from utils.sys_utils import cmd_sysctl_manage


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
            run_remove_routines(MOONRAKER_DIR)
        if remove_env:
            Logger.print_status("Removing Moonraker Python environment ...")
            run_remove_routines(MOONRAKER_ENV_DIR)

    # delete moonraker logs of all instances
    if delete_logs:
        Logger.print_status("Removing all Moonraker logs ...")
        delete_moonraker_logs(im.instances)


def select_instances_to_remove(
    instances: List[Moonraker],
) -> Union[List[Moonraker], None]:
    print_instance_overview(instances, show_index=True, show_select_all=True)

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

    cmd_sysctl_manage("daemon-reload")


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
        all_logfiles = list(instance.log_dir.glob("moonraker.log*"))
    if not all_logfiles:
        Logger.print_info("No Moonraker logs found. Skipped ...")
        return

    for log in all_logfiles:
        Logger.print_status(f"Remove '{log}'")
        run_remove_routines(log)
