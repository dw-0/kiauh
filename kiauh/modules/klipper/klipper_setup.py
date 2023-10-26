# !/usr/bin/env python

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
import subprocess
from pathlib import Path
from typing import Optional, List, Union

from kiauh.instance_manager.instance_manager import InstanceManager
from kiauh.modules.klipper.klipper import Klipper
from kiauh.modules.klipper.klipper_utils import print_instance_overview
from kiauh.utils.constants import KLIPPER_DIR, KLIPPER_ENV_DIR
from kiauh.utils.input_utils import get_user_confirm, get_user_number_input, \
    get_user_string_input, get_user_selection_input
from kiauh.utils.logger import Logger
from kiauh.utils.system_utils import parse_packages_from_file, \
    clone_repo, create_python_venv, \
    install_python_requirements, update_system_package_lists, \
    install_system_packages


def run_klipper_setup(install: bool) -> None:
    instance_manager = InstanceManager(Klipper)
    instance_list = instance_manager.get_instances()
    instances_installed = len(instance_list)

    is_klipper_installed = check_klipper_installation(instance_manager)
    if not install and not is_klipper_installed:
        Logger.print_warn("Klipper not installed!")
        return

    if install:
        add_additional = handle_existing_instances(instance_manager)
        if is_klipper_installed and not add_additional:
            Logger.print_info("Exiting Klipper setup ...")
            return

        install_klipper(instance_manager)

    if not install:
        if instances_installed == 1:
            remove_single_instance(instance_manager)
        else:
            remove_multi_instance(instance_manager)


def check_klipper_installation(instance_manager: InstanceManager) -> bool:
    instance_list = instance_manager.get_instances()
    instances_installed = len(instance_list)

    if instances_installed < 1:
        return False

    return True


def handle_existing_instances(instance_manager: InstanceManager) -> bool:
    instance_list = instance_manager.get_instances()
    instance_count = len(instance_list)

    if instance_count > 0:
        print_instance_overview(instance_list)
        if not get_user_confirm("Add new instances?"):
            return False

    return True


def install_klipper(instance_manager: InstanceManager) -> None:
    instance_list = instance_manager.get_instances()
    if_adding = " additional" if len(instance_list) > 0 else ""
    install_count = get_user_number_input(
        f"Number of{if_adding} Klipper instances to set up",
        1, default=1)

    instance_names = set_instance_names(instance_list, install_count)

    if len(instance_list) < 1:
        setup_klipper_prerequesites()

    for name in instance_names:
        current_instance = Klipper(name=name)
        instance_manager.set_current_instance(current_instance)
        instance_manager.create_instance()
        instance_manager.enable_instance()
        instance_manager.start_instance()

    instance_manager.reload_daemon()

    # step 4: check/handle conflicting packages/services

    # step 5: check for required group membership


def setup_klipper_prerequesites() -> None:
    # clone klipper TODO: read branch and url from json to allow forks
    url = "https://github.com/Klipper3D/klipper"
    branch = "master"
    clone_repo(Path(KLIPPER_DIR), url, branch)

    # install klipper dependencies and create python virtualenv
    install_klipper_packages(Path(KLIPPER_DIR))
    create_python_venv(Path(KLIPPER_ENV_DIR))
    klipper_py_req = Path(f"{KLIPPER_DIR}/scripts/klippy-requirements.txt")
    install_python_requirements(Path(KLIPPER_ENV_DIR), klipper_py_req)


def install_klipper_packages(klipper_dir: Path) -> None:
    script = f"{klipper_dir}/scripts/install-debian.sh"
    packages = parse_packages_from_file(script)
    packages = [pkg.replace("python-dev", "python3-dev") for pkg in packages]
    # Add dfu-util for octopi-images
    packages.append("dfu-util")
    # Add dbus requirement for DietPi distro
    if os.path.exists("/boot/dietpi/.version"):
        packages.append("dbus")

    update_system_package_lists(silent=False)
    install_system_packages(packages)


def set_instance_names(instance_list, install_count: int) -> List[
    Union[str, None]]:
    instance_count = len(instance_list)

    # default single instance install
    if instance_count == 0 and install_count == 1:
        return [None]

    # new multi instance install
    elif ((instance_count == 0 and install_count > 1)
          # or convert single instance install to multi instance install
          or (instance_count == 1 and install_count >= 1)):
        if get_user_confirm("Assign custom names?", False):
            return assign_custom_names(instance_count, install_count, None)
        else:
            _range = range(1, install_count + 1)
            return [str(i) for i in _range]

    # existing multi instance install
    elif instance_count > 1:
        if has_custom_names(instance_list):
            return assign_custom_names(instance_count, install_count,
                                       instance_list)
        else:
            start = get_highest_index(instance_list) + 1
            _range = range(start, start + install_count)
            return [str(i) for i in _range]


def has_custom_names(instance_list: List[Klipper]) -> bool:
    pattern = re.compile("^\d+$")
    for instance in instance_list:
        if not pattern.match(instance.name):
            return True

    return False


def assign_custom_names(instance_count: int, install_count: int,
    instance_list: Optional[List[Klipper]]) -> List[str]:
    instance_names = []
    exclude = Klipper.blacklist()

    # if an instance_list is provided, exclude all existing instance names
    if instance_list is not None:
        for instance in instance_list:
            exclude.append(instance.name)

    for i in range(instance_count + install_count):
        question = f"Enter name for instance {i + 1}"
        name = get_user_string_input(question, exclude=exclude)
        instance_names.append(name)
        exclude.append(name)

    return instance_names


def get_highest_index(instance_list: List[Klipper]) -> int:
    indices = [int(instance.name.split('-')[-1]) for instance in instance_list]
    return max(indices)


def remove_single_instance(instance_manager: InstanceManager) -> None:
    instance_list = instance_manager.get_instances()
    try:
        instance_manager.set_current_instance(instance_list[0])
        instance_manager.stop_instance()
        instance_manager.disable_instance()
        instance_manager.delete_instance(del_remnants=True)
        instance_manager.reload_daemon()
    except (OSError, subprocess.CalledProcessError):
        Logger.print_error("Removing instance failed!")
        return


def remove_multi_instance(instance_manager: InstanceManager) -> None:
    instance_list = instance_manager.get_instances()
    print_instance_overview(instance_list, show_index=True,
                            show_select_all=True)

    options = [str(i) for i in range(len(instance_list))]
    options.extend(["a", "A", "b", "B"])

    selection = get_user_selection_input(
        "Select Klipper instance to remove", options)
    print(selection)

    if selection == "b".lower():
        return
    elif selection == "a".lower():
        Logger.print_info("Removing all Klipper instances ...")
        for instance in instance_list:
            instance_manager.set_current_instance(instance)
            instance_manager.stop_instance()
            instance_manager.disable_instance()
            instance_manager.delete_instance(del_remnants=True)
    else:
        instance = instance_list[int(selection)]
        Logger.print_info(
            f"Removing Klipper instance: {instance.get_service_file_name()}")
        instance_manager.set_current_instance(instance)
        instance_manager.stop_instance()
        instance_manager.disable_instance()
        instance_manager.delete_instance(del_remnants=False)

    instance_manager.reload_daemon()
