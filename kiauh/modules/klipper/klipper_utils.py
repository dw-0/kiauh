#!/usr/bin/env python3

# ======================================================================= #
#  Copyright (C) 2020 - 2023 Dominik Willner <th33xitus@gmail.com>        #
#                                                                         #
#  This file is part of KIAUH - Klipper Installation And Update Helper    #
#  https://github.com/dw-0/kiauh                                          #
#                                                                         #
#  This file may be distributed under the terms of the GNU GPLv3 license  #
# ======================================================================= #

import os
import re
import grp
import subprocess
import textwrap

from typing import List, Union

from kiauh.core.instance_manager.instance_manager import InstanceManager
from kiauh.modules.klipper.klipper import Klipper
from kiauh.modules.klipper.klipper_dialogs import (
    print_missing_usergroup_dialog,
    print_select_custom_name_dialog,
)
from kiauh.utils.constants import CURRENT_USER
from kiauh.utils.input_utils import get_confirm, get_string_input
from kiauh.utils.logger import Logger
from kiauh.utils.system_utils import mask_system_service


def assign_custom_names(
    instance_count: int, install_count: int, instance_list: List[Klipper] = None
) -> List[str]:
    instance_names = []
    exclude = Klipper.blacklist()

    # if an instance_list is provided, exclude all existing instance suffixes
    if instance_list is not None:
        for instance in instance_list:
            exclude.append(instance.suffix)

    for i in range(instance_count + install_count):
        question = f"Enter name for instance {i + 1}"
        name = get_string_input(question, exclude=exclude)
        instance_names.append(name)
        exclude.append(name)

    return instance_names


def handle_convert_single_to_multi_instance_names(
    install_count: int,
) -> Union[List[str], None]:
    print_select_custom_name_dialog()
    choice = get_confirm("Assign custom names?", False, allow_go_back=True)
    if choice is True:
        # instance_count = 0 and install_count + 1 as we want to assign a new name to the existing single install
        return assign_custom_names(0, install_count + 1)
    elif choice is False:
        # "install_count + 2" as we need to account for the existing single install
        _range = range(1, install_count + 2)
        return [str(i) for i in _range]

    return None


def handle_new_multi_instance_names(
    instance_count: int, install_count: int
) -> Union[List[str], None]:
    print_select_custom_name_dialog()
    choice = get_confirm("Assign custom names?", False, allow_go_back=True)
    if choice is True:
        return assign_custom_names(instance_count, install_count)
    elif choice is False:
        _range = range(1, install_count + 1)
        return [str(i) for i in _range]

    return None


def handle_existing_multi_instance_names(
    instance_count: int, install_count: int, instance_list: List[Klipper]
) -> List[str]:
    if has_custom_names(instance_list):
        return assign_custom_names(instance_count, install_count, instance_list)
    else:
        start = get_highest_index(instance_list) + 1
        _range = range(start, start + install_count)
        return [str(i) for i in _range]


def handle_single_to_multi_conversion(
    instance_manager: InstanceManager, name: str
) -> None:
    instance_list = instance_manager.instances
    instance_manager.current_instance = instance_list[0]
    old_data_dir_name = instance_manager.instances[0].data_dir
    instance_manager.stop_instance()
    instance_manager.disable_instance()
    instance_manager.delete_instance(del_remnants=False)
    instance_manager.current_instance = Klipper(suffix=name)
    new_data_dir_name = instance_manager.current_instance.data_dir
    try:
        os.rename(old_data_dir_name, new_data_dir_name)
    except OSError as e:
        log = f"Cannot rename {old_data_dir_name} to {new_data_dir_name}:\n{e}"
        Logger.print_error(log)


def check_user_groups():
    current_groups = [grp.getgrgid(gid).gr_name for gid in os.getgroups()]

    missing_groups = []
    if "tty" not in current_groups:
        missing_groups.append("tty")
    if "dialout" not in current_groups:
        missing_groups.append("dialout")

    if not missing_groups:
        return

    print_missing_usergroup_dialog(missing_groups)
    if not get_confirm(f"Add user '{CURRENT_USER}' to group(s) now?"):
        log = "Skipped adding user to required groups. You might encounter issues."
        Logger.warn(log)
        return

    try:
        for group in missing_groups:
            Logger.print_status(f"Adding user '{CURRENT_USER}' to group {group} ...")
            command = ["sudo", "usermod", "-a", "-G", group, CURRENT_USER]
            subprocess.run(command, check=True)
            Logger.print_ok(f"Group {group} assigned to user '{CURRENT_USER}'.")
    except subprocess.CalledProcessError as e:
        Logger.print_error(f"Unable to add user to usergroups: {e}")
        raise

    log = "Remember to relog/restart this machine for the group(s) to be applied!"
    Logger.print_warn(log)


def handle_disruptive_system_packages() -> None:
    services = []

    command = ["systemctl", "is-enabled", "brltty"]
    brltty_status = subprocess.run(command, capture_output=True, text=True)

    command = ["systemctl", "is-enabled", "brltty-udev"]
    brltty_udev_status = subprocess.run(command, capture_output=True, text=True)

    command = ["systemctl", "is-enabled", "ModemManager"]
    modem_manager_status = subprocess.run(command, capture_output=True, text=True)

    if "enabled" in brltty_status.stdout:
        services.append("brltty")
    if "enabled" in brltty_udev_status.stdout:
        services.append("brltty-udev")
    if "enabled" in modem_manager_status.stdout:
        services.append("ModemManager")

    for service in services if services else []:
        try:
            log = f"{service} service detected! Masking {service} service ..."
            Logger.print_status(log)
            mask_system_service(service)
            Logger.print_ok(f"{service} service masked!")
        except subprocess.CalledProcessError:
            warn_msg = textwrap.dedent(
                f"""
                KIAUH was unable to mask the {service} system service. 
                Please fix the problem manually. Otherwise, this may have 
                undesirable effects on the operation of Klipper.
                """
            )[1:]
            Logger.print_warn(warn_msg)


def has_custom_names(instance_list: List[Klipper]) -> bool:
    pattern = re.compile("^\d+$")
    for instance in instance_list:
        if not pattern.match(instance.suffix):
            return True

    return False


def get_highest_index(instance_list: List[Klipper]) -> int:
    indices = [int(instance.suffix.split("-")[-1]) for instance in instance_list]
    return max(indices)
