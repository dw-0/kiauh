# ======================================================================= #
#  Copyright (C) 2020 - 2024 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #
from __future__ import annotations

from typing import List

from components.klipper import KLIPPER_DIR, KLIPPER_ENV_DIR
from components.klipper.klipper import Klipper
from components.klipper.klipper_dialogs import print_instance_overview
from core.instance_manager.instance_manager import InstanceManager
from core.logger import Logger
from core.services.message_service import Message
from core.types.color import Color
from utils.fs_utils import run_remove_routines
from utils.input_utils import get_selection_input
from utils.instance_utils import get_instances
from utils.sys_utils import unit_file_exists


def run_klipper_removal(
    remove_service: bool,
    remove_dir: bool,
    remove_env: bool,
) -> Message:
    completion_msg = Message(
        title="Klipper Removal Process completed",
        color=Color.GREEN,
    )
    klipper_instances: List[Klipper] = get_instances(Klipper)

    if remove_service:
        Logger.print_status("Removing Klipper instances ...")
        if klipper_instances:
            instances_to_remove = select_instances_to_remove(klipper_instances)
            remove_instances(instances_to_remove)
            instance_names = [i.service_file_path.stem for i in instances_to_remove]
            txt = f"● Klipper instances removed: {', '.join(instance_names)}"
            completion_msg.text.append(txt)
        else:
            Logger.print_info("No Klipper Services installed! Skipped ...")

    if (remove_dir or remove_env) and unit_file_exists("klipper", suffix="service"):
        completion_msg.text = [
            "Some Klipper services are still installed:",
            f"● '{KLIPPER_DIR}' was not removed, even though selected for removal.",
            f"● '{KLIPPER_ENV_DIR}' was not removed, even though selected for removal.",
        ]
    else:
        if remove_dir:
            Logger.print_status("Removing Klipper local repository ...")
            if run_remove_routines(KLIPPER_DIR):
                completion_msg.text.append("● Klipper local repository removed")
        if remove_env:
            Logger.print_status("Removing Klipper Python environment ...")
            if run_remove_routines(KLIPPER_ENV_DIR):
                completion_msg.text.append("● Klipper Python environment removed")

    if completion_msg.text:
        completion_msg.text.insert(0, "The following actions were performed:")
    else:
        completion_msg.color = Color.YELLOW
        completion_msg.centered = True
        completion_msg.text = ["Nothing to remove."]

    return completion_msg


def select_instances_to_remove(instances: List[Klipper]) -> List[Klipper] | None:
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
    selection = get_selection_input("Select Klipper instance to remove", options)

    instances_to_remove = []
    if selection == "b":
        return None
    elif selection == "a":
        instances_to_remove.extend(instances)
    else:
        instances_to_remove.append(instance_map[selection])

    return instances_to_remove


def remove_instances(
    instance_list: List[Klipper] | None,
) -> None:
    if not instance_list:
        return

    for instance in instance_list:
        Logger.print_status(f"Removing instance {instance.service_file_path.stem} ...")
        InstanceManager.remove(instance)
        delete_klipper_env_file(instance)


def delete_klipper_env_file(instance: Klipper):
    Logger.print_status(f"Remove '{instance.env_file}'")
    if not instance.env_file.exists():
        msg = f"Env file in {instance.base.sysd_dir} not found. Skipped ..."
        Logger.print_info(msg)
        return
    run_remove_routines(instance.env_file)
